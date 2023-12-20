import uvicorn
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
import httpx
import json
import logging
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fuzzywuzzy import fuzz
from typing import List, Union
import uvicorn
from typing import List, Dict, Union
 
app = FastAPI()
templates = Jinja2Templates(directory="templates")
 
#logging.basicConfig(level=logging.DEBUG)

def convert_string_to_list(input_str: str) -> List[str]:
    # Remove leading and trailing whitespaces, and split by ','
    return [element.strip() for element in input_str.strip('[]').split(',')]
 
 
def compare_lists_with_fuzzy(l1, l2, threshold=50):
    matching_elements_l1 = []
    matching_elements_l2 = []
    non_matching_elements_l1 = []
    non_matching_elements_l2 = []
 
    for element_l1 in l1:
        max_similarity = 0
        matching_element_l2 = ''
 
        for element_l2 in l2:
            similarity = fuzz.ratio(
                str(element_l1).lower(), str(element_l2).lower()
            )  # Convert to lowercase for case-insensitive comparison
            if similarity > max_similarity and similarity >= threshold:
                max_similarity = similarity
                matching_element_l2 = element_l2
 
        if matching_element_l2:
            matching_elements_l1.append(element_l1.strip("'"))
            matching_elements_l2.append(matching_element_l2.strip("'"))
        else:
            non_matching_elements_l1.append(element_l1.strip("'"))
 
    non_matching_elements_l2 = [
        element_l2.strip("'")
        for element_l2 in l2
        if element_l2.strip("'") not in matching_elements_l2
    ]
 
    # print("Matching Elements in l1:", matching_elements_l1)
    # print("Matching Elements in l2:", matching_elements_l2)
    # print("Non-Matching Elements in l1:", non_matching_elements_l1)
    # print("Non-Matching Elements in l2:", non_matching_elements_l2)
 
    similar_elements = []
    for element_l1, element_l2 in zip(matching_elements_l1, matching_elements_l2):
        similar_elements.append({"element_name_l1": element_l1, "element_name_l2": element_l2})
 
    result = {"similar_elements": similar_elements}
    return result
 
 
def generate_final_response(similar_elements: List[Dict[str, str]], response_data: List[Dict[str, str]]) -> List[Dict[str, Union[str, int]]]:
    final_response = []
    processed_labels = set()

    # Create a dictionary for easy lookup of response_data based on labels
    response_lookup = {data['label']: data for data in response_data}

    for element in similar_elements:
        # Find matching element in response_data based on label
        matched_data = next((data for data in response_data if data['label'] == element['element_name_l1']), None)

        if matched_data:
            final_response.append({
                'jsonPath': matched_data['jsonPath'],
                'l2_matched': element['element_name_l2'],
                'datatype': matched_data['dataType'],
                'value': matched_data['value']
            })
            processed_labels.add(element['element_name_l1'])  # Track processed labels

    # Handle unmatched elements from l1
    for data in response_data:
        if data['label'] not in processed_labels:
            final_response.append({
                'jsonPath': data['jsonPath'],
                'l2_matched': '',  # No match from l2
                'datatype': data['dataType'],
                'value': data['value']  # Use value from response_data
            })

    return final_response


@app.post('/process_data')
async def process_data(request: Request, data_url: str = Form(...)):
    try:
        #logging.debug(f"Processing data from URL: {data_url}")
 
        # Fetch JSON data from the specified URL using httpx for asynchronous requests
        async with httpx.AsyncClient() as client:
            response = await client.get(data_url)
 
        if response.status_code == 200:
            # Assuming the response contains JSON data, you can parse it
            json_data = response.json()
 
            if isinstance(json_data, list) and len(json_data) > 0:
                sample_record = json_data[0]
 
                # Send the sample record to OpenAI for schema extraction
                openai_url = 'https://cymetriopen.openai.azure.com/openai/deployments/instructionalmodel/completions?api-version=2023-09-15-preview'
                openai_headers = {
                    'Content-Type': 'application/json',
                    'api-key': 'ebe64320148849aead404cc3aec9cc49'
                }
 
                openai_payload = {
                    "prompt": f"Give me list of fields as jsonPath and labels and datatype and value in this json sample {sample_record}",
                    "max_tokens": 800,
                    "temperature": 0.2,
                    "frequency_penalty": 0,
                    "presence_penalty": 0,
                    "top_p": 1,
                    "stop": None
                }
 
                try:
                    async with httpx.AsyncClient() as openai_client:
                        openai_response = await openai_client.post(openai_url, headers=openai_headers, json=openai_payload)
                        openai_response.raise_for_status()
 
                        # Extract only the text part from the OpenAI response
                        response_text = openai_response.json()['choices'][0]['text']
 
                        # Parse the response_text into a list of dictionaries
                        response_data = json.loads(response_text)
 
                        #logging.debug(f"Received response from OpenAI: {response_data}")
                        
                    
                        l1 = [item['label'] for item in response_data]

                        if isinstance(l1, str):
                            l1_list = convert_string_to_list(l1)
                        else:
                            l1_list = l1

                        l2 = [' Id', 'Displayname', 'Firstname', 'Lastname', 'Country', 'Mobile', 'Email', 'Status', 'Created', 'Updated', 'Created By', 'Updated By', 'Assignedgroups', 'Provisionedapps', 'Attributes', 'Rbacroles', 'Version', ' Class']

                        if isinstance(l2, str):
                            l2_list = convert_string_to_list(l2)
                        else:
                            l2_list = l2

                        threshold = 65

                        result = compare_lists_with_fuzzy(l1_list, l2_list, threshold)

                        final_response = generate_final_response(result['similar_elements'], response_data)

                        return JSONResponse(content=final_response)

                except httpx.HTTPError as errh:
                    #logging.error(f"HTTP Error: {errh}")
                    raise HTTPException(status_code=500, detail=f"HTTP Error: {errh}")
                except httpx.RequestError as err:
                    #logging.error(f"Request Exception: {err}")
                    raise HTTPException(status_code=500, detail=f"Request Exception: {err}")
            else:
                return "No records found in the JSON data."
        else:
            raise HTTPException(status_code=response.status_code, detail=f"API call to fetch data failed with status code {response.status_code}")
    except Exception as e:
        #logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
 
    return JSONResponse(content=result)





if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)