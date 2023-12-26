import uvicorn
from fastapi import FastAPI, Form, Request, HTTPException
import httpx
import json
import logging
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from fuzzywuzzy import fuzz
from typing import List, Union
import uvicorn
from typing import List, Dict, Union
from database.connection import get_collection
 
app = FastAPI()
 
logging.basicConfig(level=logging.DEBUG)

def stored_input(tenant: str):
    #logging.debug(f"Getting collection for tenant: {tenant}")
    return get_collection(tenant, "openai_input")

def stored_response(tenant: str):
    #logging.debug(f"Getting collection for storing scores for tenant: {tenant}")
    return get_collection(tenant, "openai_output")
 
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
            el1 = str(element_l1).lower()
            el2 = str(element_l2).lower()
            similarity = fuzz.ratio(
                el1, el2
            )
            #print(f'l1 {el1} ;;; l2 {el2} ;; similarity {similarity}')  # Convert to lowercase for case-insensitive comparison
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
                'datatype': matched_data['datatype'],
                'value': matched_data['value']
            })
            processed_labels.add(element['element_name_l1'])  # Track processed labels
 
    # Handle unmatched elements from l1
    for data in response_data:
        if data['label'] not in processed_labels:
            final_response.append({
                'jsonPath': data['jsonPath'],
                'l2_matched': '',  # No match from l2
                'datatype': data['datatype'],
                'value': data['value']  # Use value from response_data
            })
 
    return final_response
 

@app.post('/generativeaisrvc/send_and_get_sample')
async def process_data(request: Request, data: dict):
    response_data = {}
    try:
        tenant = "generativeAI"
        input_collection =  stored_input(tenant)
        output_collection =  stored_response(tenant)

        #input_collection.insert_one(data)
        input_collection.update_one(
            {"appId": data["appId"]},
            {"$set": data},
            upsert=True
        )
        
        logging.debug("Input respone saved successfully")
        print("data :",data)
 
        def extract_info(json_data):
            appId = json_data.get("appId")
            body = ""
            params = None
            headers = None
            try:
                body = json.loads(json_data["schema"]["nodes"][0]["data"]["body"])
            except:
                print("body not found")


            try:
                headers = {header["key"]: header["value"] for header in json_data["schema"]["nodes"][0]["data"]["headers"]}
            except:
                print("headers not found")

            url = json_data["schema"]["nodes"][0]["data"]["url"]
            request_method = json_data["schema"]["nodes"][0]["data"]["requestMethod"]
            try:
                params_list = json_data["schema"]["nodes"][0]["data"]["params"]
                params = {param["key"]: param["value"] for param in params_list if param["included"]}
            except:
                print("params not found")

            print("appId: ",appId)
            print("body: ",body)
            print("headers: ",headers)
            #print("url: ",url)
            print("request_method: ",request_method)
            print("params: ",params)
            return appId, body, headers, url, request_method, params
 
        appId, body, headers, url, request_method, params = extract_info(data)
       

        final_url = url
 
        if params:
            final_url += "?" + "&".join(f"{key}={value}" for key,value in params.items())
 
        print("final_url: ",final_url)
 
 
        # Fetch JSON data from the specified URL using httpx for asynchronous requests
        async with httpx.AsyncClient() as client:
            #url_from_request = data["url"]
            #print("url_from_request: ",url)
            requestMethod_from_request = request_method
            #print("requestMethod_from_request: ",requestMethod_from_request)
 
            match requestMethod_from_request:
                case "GET":
                    # Call method for GET request
                    response = await client.get(url=final_url, headers=headers)
                    print("response: ",response)
               
                # case "POST":
                #     # Call method for POST request
                #     ## if body is empty, skip the data field
                #     ## if body is not empty, use as below
                #     response = client.post(url=url_from_request)
                #     print("response: ",response)
                # case "PUT":
                #     # Handle other request methods
                #     response = client.put(url=request.data.url, data=body_dict)
 
                # case "PATCH":
                #     response = client.patch(url=request.data.url, data=body_dict)
                  
                # case "DELETE":
                #     response = client.delete(url=request.data.url)
               
 
        if response.status_code >= 200 or response.status_code <= 204:
            # Assuming the response contains JSON data, you can parse it
            json_data = response.json()
            print("json_data: ",json_data)
            '''
            users_array = json_data['users'][0]
            users_json = json.dumps(users_array, indent=4)
            print(users_json)
            print("shreyas")
            '''
            json_data = json_data['users']
           
            #print("json_data: ",json_data)
 
            if isinstance(json_data, list) and len(json_data) > 0:
                sample_record = json.dumps(json_data[0])
                #sample_dict = {}
                #sample_dict['primaryEmail'] = sample_record['primaryEmail']
                print("sample_record: ",sample_record)
                response_data = json_data[0]
               
    except Exception as e:
        print(e)

    #return response_data
    return JSONResponse(content=response_data, media_type="application/json")

 
@app.post('/generativeaisrvc/process_data')
async def process_data(request: Request, data: dict):
    try:
        tenant = "generativeAI"
        input_collection =  stored_input(tenant)
        output_collection =  stored_response(tenant)

        #input_collection.insert_one(data)
        input_collection.update_one(
            {"appId": data["appId"]},
            {"$set": data},
            upsert=True
        )

        logging.debug("Input respone saved successfully")
        print("data :",data)
 
        def extract_info(json_data):
            appId = json_data.get("appId")
            body = ""
            params = None
            headers = None
            try:
                body = json.loads(json_data["schema"]["nodes"][0]["data"]["body"])
            except:
                print("body not found")


            try:
                headers = {header["key"]: header["value"] for header in json_data["schema"]["nodes"][0]["data"]["headers"]}
            except:
                print("headers not found")

            url = json_data["schema"]["nodes"][0]["data"]["url"]
            request_method = json_data["schema"]["nodes"][0]["data"]["requestMethod"]
            try:
                params_list = json_data["schema"]["nodes"][0]["data"]["params"]
                params = {param["key"]: param["value"] for param in params_list if param["included"]}
            except:
                print("params not found")

            print("appId: ",appId)
            print("body: ",body)
            print("headers: ",headers)
            #print("url: ",url)
            print("request_method: ",request_method)
            print("params: ",params)
            return appId, body, headers, url, request_method, params
 
        appId, body, headers, url, request_method, params = extract_info(data)
       

        final_url = url
 
        if params:
            final_url += "?" + "&".join(f"{key}={value}" for key,value in params.items())
 
        print("final_url: ",final_url)
 
 
        # Fetch JSON data from the specified URL using httpx for asynchronous requests
        async with httpx.AsyncClient() as client:
            #url_from_request = data["url"]
            #print("url_from_request: ",url)
            requestMethod_from_request = request_method
            #print("requestMethod_from_request: ",requestMethod_from_request)
 
            match requestMethod_from_request:
                case "GET":
                    # Call method for GET request
                    response = await client.get(url=final_url, headers=headers)
                    print("response: ",response)
               
                # case "POST":
                #     # Call method for POST request
                #     ## if body is empty, skip the data field
                #     ## if body is not empty, use as below
                #     response = client.post(url=url_from_request)
                #     print("response: ",response)
                # case "PUT":
                #     # Handle other request methods
                #     response = client.put(url=request.data.url, data=body_dict)
 
                # case "PATCH":
                #     response = client.patch(url=request.data.url, data=body_dict)
                  
                # case "DELETE":
                #     response = client.delete(url=request.data.url)
               
 
        if response.status_code >= 200 or response.status_code <= 204:
            # Assuming the response contains JSON data, you can parse it
            json_data = response.json()
            print("json_data: ",json_data)
            '''
            users_array = json_data['users'][0]
            users_json = json.dumps(users_array, indent=4)
            print(users_json)
            print("shreyas")
            '''
            json_data = json_data['users']
           
            #print("json_data: ",json_data)
 
            if isinstance(json_data, list) and len(json_data) > 0:
                sample_record = json.dumps(json_data[0])
                #sample_dict = {}
                #sample_dict['primaryEmail'] = sample_record['primaryEmail']
                print("sample_record: ",sample_record)
               
                # Send the sample record to OpenAI for schema extraction
                openai_url = 'https://cymetriopen.openai.azure.com/openai/deployments/instructionalmodel/completions?api-version=2023-09-15-preview'
                openai_headers = {
                    'Content-Type': 'application/json',
                    'api-key': 'ebe64320148849aead404cc3aec9cc49'
                }
 
                openai_payload = {
                    "prompt": "Give me list of fields as jsonPath and labels and datatype and value in this json sample in json format only,keep all fields in lowercase only"+sample_record,
                    "max_tokens": 8000,
                    "temperature": 0.2,
                    "frequency_penalty": 0,
                    "presence_penalty": 0,
                    "top_p": 1,
                    "stop": None
                }
 
                try:
                    print("declaring async client")
                    async with httpx.AsyncClient(timeout=360) as openai_client:
                        print("start of openai request")
                        print(f'url  is {openai_url}')
                        #print(f'headers are {openai_headers}')
                        #print(f'payload is {openai_payload}')
                        openai_response = ''
                        try:
                            openai_response = await openai_client.post(openai_url, headers=openai_headers, json=openai_payload,timeout=300)
                        except Exception as e:
                            print(f'openai response {openai_response}')
                            print(e)
                        finally:
                            print(f'openai response {openai_response}')
 
                        #openai_response.raise_for_status()
                        print(f'Respoinse freom openai is {openai_response}')
                        # Extract only the text part from the OpenAI response
                        response_text = openai_response.json()['choices'][0]['text']
                        print(f'response text is {response_text}')
                       
                        #Parse the response_text into a list of dictionaries
                        response_data = json.loads(response_text)
                        print(f'response data is {response_data}')
                        logging.debug(f"Received response from OpenAI: {response_data}")
                       
                   
                        l1 = [item['label'] for item in response_data]
 
                        if isinstance(l1, str):
                            l1_list = convert_string_to_list(l1)
                        else:
                            l1_list = l1
 
                        l2 = ['Id', 'Displayname', 'Firstname', 'Lastname', 'Country', 'Mobile', 'Email', 'Status', 'Created', 'Updated', 'Created By', 'Updated By', 'Assignedgroups', 'Provisionedapps', 'Attributes', 'Rbacroles', 'Version', ' Class']
 
                        if isinstance(l2, str):
                            l2_list = convert_string_to_list(l2)
                        else:
                            l2_list = l2
 
                        threshold = 55
 
                        result = compare_lists_with_fuzzy(l1_list, l2_list, threshold)
 
                        final_response = generate_final_response(result['similar_elements'], response_data)
                        final_response_dict = {"final_response": final_response}

                        output_collection.insert_one(final_response_dict)
                        final_response_dict['appId'] = appId
                        output_collection.update_one(
                            {"appId": appId},
                            {"$set": final_response_dict},
                            upsert=True
                        )


                        logging.debug("Final response saved successfully")


                        #print(f'final response is {final_response}')
                        return JSONResponse(content=final_response)
 
                except Exception as errh:
                    print(f"HTTP Error {errh} is: {errh}")
                    #raise HTTPException(status_code=500, detail=f"HTTP Error: {errh}")
               
            else:
                return "No records found in the JSON data."
        else:
            raise HTTPException(status_code=response.status_code, detail=f"API call to fetch data failed with status code {response.status_code}")
    except Exception as e:
        #logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
 
 
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5001)