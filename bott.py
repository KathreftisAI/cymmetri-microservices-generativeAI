from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fuzzywuzzy import fuzz
from typing import List, Union
import uvicorn
 
app = FastAPI()
 
 
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
 
 
@app.post("/compare", response_model=dict)
def compare_lists(
    l1: Union[str, List[str]] = Form(...),
    l2: Union[str, List[str]] = Form(...),
    threshold: int = Form(70, gt=0, le=100),
):
    if isinstance(l1, str):
        l1_list = convert_string_to_list(l1)
    else:
        l1_list = l1
 
    if isinstance(l2, str):
        l2_list = convert_string_to_list(l2)
    else:
        l2_list = l2
 
    result = compare_lists_with_fuzzy(l1_list, l2_list, threshold)

    print("result: ",result)
 
    return JSONResponse(content=result)
 
 
# Route to serve the index.html file
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("templates/index.html", "r") as file:
        return file.read()
 
 
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)