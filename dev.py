import uvicorn
from fastapi import FastAPI, Form, Request, HTTPException, Header
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
from dateutil.parser import parse
from datetime import datetime
from datetime import date
import datetime
import json
from typing import Dict, Any, List
from fuzzywuzzy import process
import uvicorn

app = FastAPI()
 
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(filename)s on %(lineno)d: %(message)s',
)

def stored_input(tenant: str):
    #logging.debug(f"Getting collection for tenant: {tenant}")
    return get_collection(tenant, "schema_maker_input")

def stored_response(tenant: str):
    #logging.debug(f"Getting collection for storing scores for tenant: {tenant}")
    return get_collection(tenant, "schema_maker_output")

def convert_string_to_list(input_str: str) -> List[str]:
    # Remove leading and trailing whitespaces, and split by ','
    return [element.strip() for element in input_str.strip('[]').split(',')]


#-----------------------------extracting the user object from response-----------------

def extract_user_data(response):
    logging.debug(f"extracting the users from the nested json")
    user_data_list = []

    def is_user_data(obj):
        # Check if object contains at least one of the common user data keys
        user_keys = {'displayName', 'givenName' 'email', 'id', 'DateOfBirth'}
        return any(key in obj for key in user_keys)

    def traverse(obj):
        # Recursively traverse the JSON object
        nonlocal user_data_list
        if isinstance(obj, dict):
            if is_user_data(obj):
                user_data_list.append(obj)
            else:
                for value in obj.values():
                    traverse(value)
        elif isinstance(obj, list):
            for item in obj:
                traverse(item)

    traverse(response)

    return user_data_list

#---------------------------extracting keys, datatype, label and jsonpath----------------

def get_distinct_keys_and_datatypes(json_data):
    logging.debug(f"extracting the properties from the json data")
    distinct_keys_datatypes = []

    def explore_json(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                if isinstance(value, dict) or isinstance(value, list):
                    explore_json(value, new_path)
                else:
                    datatype = get_data_type(value)
                    distinct_keys_datatypes.append({
                        "jsonpath": new_path,
                        "label": key,
                        "datatype": datatype,
                        "value": value
                    })
        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                new_path = f"{path}.{index}" if path else str(index)
                if isinstance(item, dict):
                    explore_json(item, new_path)
                else:
                    datatype = get_data_type(item)
                    distinct_keys_datatypes.append({
                        "jsonpath": new_path,
                        "label": f"Index {index}",
                        "datatype": datatype,
                        "value": item
                    })

    def get_data_type(value):
        if isinstance(value, str):
            try:
                # Try parsing the value as a date
                parse_result = parse(value)
                if (parse_result.strftime('%Y-%m-%d') == value) or (parse_result.strftime('%d-%m-%y') == value):
                    return 'DATE'  # Date if the parsed value matches one of the date formats
                else:
                    if parse_result.time() != datetime.time(0, 0, 0):
                        return 'DATETIME'
                    else:
                        return 'STRING'
            except (ValueError, OverflowError):
                return 'STRING'  # Fallback to string if parsing as date/datetime fails
        elif isinstance(value, bool):
            return 'BOOLEAN'
        elif isinstance(value, int):
            return 'INTEGER'
        elif isinstance(value, float):
            return 'FLOAT'
        elif isinstance(value, list):
            return 'ARRAY'
        elif value is None:
            return None  # Custom type for null values
        else:
            return 'CUSTOM'


    explore_json(json_data)
    return distinct_keys_datatypes

#-------------------fuzzy logic matching function----------------------

def compare_lists_with_fuzzy(l1, l2, threshold=50):
    logging.debug(f"comparing logic for list1 and list2")
    
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

#----------------------generates final response---------------
def generate_final_response(similar_elements: List[Dict[str, str]], response_data: List[Dict[str, str]], l2_datatypes: Dict[str, str]) -> List[Dict[str, Union[str, int]]]:
    logging.debug(f"Beautifying the response for saving into the collection")
    final_response = []
    processed_labels = set()
 
    # Create a dictionary for easy lookup of response_data based on labels
    response_lookup = {data['label']: data for data in response_data}
 
    for element in similar_elements:
        # Find matching element in response_data based on label
        matched_data = next((data for data in response_data if data['label'] == element['element_name_l1']), None)
 
        if matched_data:
            l2_datatype = l2_datatypes.get(element['element_name_l2'], None)
            final_response.append({
                'jsonPath': matched_data['jsonpath'],
                'attributeName': element['element_name_l1'],
                'l1_datatype': matched_data['datatype'],
                'l2_matched': element['element_name_l2'],
                'l2_datatype': l2_datatype,
                'value': matched_data['value']
            })
            processed_labels.add(element['element_name_l1'])  # Track processed labels

        else:
            print(f"No matched data found for {element['element_name_l1']}")
 
    # Handle unmatched elements from l1
    for data in response_data:
        if data['label'] not in processed_labels:
            final_response.append({
                'jsonPath': data['jsonpath'],
                'attributeName': data['label'],
                'l1_datatype': data['datatype'],
                'l2_matched': '',  # No match from l2
                'l2_datatype': '',
                'value': data['value']  # Use value from response_data
            })
 
    return final_response

def map_field_to_policy(field: str, policy_mapping: List[Dict[str, Any]]) -> str:
    matched = False
    # Perform case-insensitive exact match
    for map_entry in policy_mapping:
        external_field = map_entry["external"]
        internal_field = map_entry["internal"]
        if external_field.lower() == field.lower():
            matched = True
            print(f"Exact match found: '{field}' -> '{external_field}'")
            return external_field, f"${{{external_field}}}"  # Use placeholder syntax
    
    # Perform fuzzy matching if no direct match is found
    best_match, score = process.extractOne(field.lower(), [map_entry["internal"].lower() for map_entry in policy_mapping])
    if score >= 70:  # Adjust the threshold as needed
        for map_entry in policy_mapping:
            if map_entry["internal"].lower() == best_match:
                matched = True
                print(f"Fuzzy match found: '{field}' -> '{map_entry['external']}' (Best match: '{best_match}')")
                return map_entry['external'], f"${{{map_entry['external']}}}"  # Use placeholder syntax
    
    if not matched:
        print(f"No match found for '{field}'")
    return field, None  # Return original field if no match is found


def map_nested_fields_to_policy(nested_field: Dict[str, Any], policy_mapping: List[Dict[str, Any]]) -> Dict[str, Any]:
    mapped_nested_data = {}
    for field, value in nested_field.items():
        if isinstance(value, dict):
            # Recursively map nested fields
            mapped_nested_data[field] = map_nested_fields_to_policy(value, policy_mapping)
        else:
            # Map non-nested fields
            mapped_field, placeholder = map_field_to_policy(field, policy_mapping)
            if placeholder is not None:
                mapped_nested_data[field] = placeholder
            else:
                mapped_nested_data[field] = value
    return mapped_nested_data



## Read header as tenant
#----------------------api for policy mapping-----------------------------
@app.post('/generativeaisrvc/get_policy_mapped')
async def get_mapped(data: dict, tenant: str = Header(None)):
    print("Headers:", tenant)
    logging.debug(f"API call for auto policy mapping with the application")
    try:
        
        input_collection =  stored_input(tenant)
        output_collection =  stored_response(tenant)

        # Store the received response directly into the input collection
        #input_collection.insert_one(data)
        
        logging.debug("Input respone saved successfully")
        print("data :",data)
 
        #appId = data['appId']
               
        # Assuming the response contains JSON data, you can parse it
        
        #Start of changes by Abhishek
        
        json_data = data.get('payload')

        print("json data is {}", json_data)
        #End of changes by Abhishek

        json_data_ = extract_user_data(json_data)
        print("json_data: ",json_data_)

        response_data = get_distinct_keys_and_datatypes(json_data_)
        #response_data=list(response_data.values())

        l1 = [item['label'] for item in response_data]

        if isinstance(l1, str):
            l1_list = set(convert_string_to_list(l1))
            print("list1: ",l1_list)
        else:
            l1_list = set(l1)
            print("list1: ",l1_list)


        l2 = ['department', 'employeeId', 'designation', 'appUpdatedDate', 'displayName', 'mobile', 'country', 'city', 'email', 'end_date', 'firstName', 'login', 'lastName', 'userType', 'dateOfBirth', 'endDate', 'startDate', 'password', 'status', 'profilePicture', 'appUserId', 'landline']

        l2_datatypes = {
                        'department': 'STRING',
                        'employeeId': 'STRING',
                        'designation': 'STRING',
                        'appUpdatedDate': 'DATETIME',
                        'displayName': 'STRING',    
                        'mobile': 'STRING',
                        'country': 'STRING',
                        'city': 'STRING',
                        'email': 'STRING',
                        'end_date': 'DATE',
                        'firstName': 'STRING',
                        'login': 'INTEGER',
                        'lastName': 'STRING',
                        'userType': 'STRING',
                        'end_date': 'DATE',
                        'login': 'INTEGER',
                        'userType': 'STRING',
                        'dateOfBirth': 'DATE',
                        'endDate': 'DATE',
                        'startDate': 'DATE',
                        'password': 'password',
                        'status': 'STRING',
                        'profilePicture': 'profilePicture',
                        'appUserId': 'STRING',
                        'landline': 'STRING'
                    }
        
        if isinstance(l2, str):
            l2_list = convert_string_to_list(l2)
        else:
            l2_list = l2

        threshold = 60

        result = compare_lists_with_fuzzy(l1_list, l2_list, threshold)

        final_response = generate_final_response(result['similar_elements'], response_data, l2_datatypes)
        final_response_dict = {"final_response": final_response}

        # Assuming 'appId' is present in the received response
        appId = data.get("appId")
        final_response_dict['appId'] = appId

        output_collection.update_one(
            {"appId": appId},
            {"$set": final_response_dict},
            upsert=True
        )

        subset_response = output_collection.aggregate([
            {"$unwind": "$final_response"},
            {"$match": {"final_response.value": {"$ne": None}, "appId": appId}}, 
            {"$group": {
                "_id": "$final_response.attributeName",
                "data": {"$first": "$final_response"}
            }},
            {"$project": {
                "_id": 0,
                "jsonPath": "$data.jsonPath",
                "attributeName": "$data.attributeName",
                "l1_datatype": "$data.l1_datatype",
                "l2_matched": "$data.l2_matched",
                "l2_datatype": "$data.l2_datatype",
                "value": "$data.value",
                "similarity_percentage": "$data.similarity_percentage",
                "confidence": "$data.confidence"
            }}
        ])

        subset_response_data = list(subset_response)

        # Serialize each document into a JSON serializable format
        json_serializable_response = []
        for doc in subset_response_data:
            json_serializable_doc = {
                "jsonPath": doc["jsonPath"],
                "attributeName": doc["attributeName"],
                "l1_datatype": doc["l1_datatype"],
                "l2_matched": doc["l2_matched"],
                "l2_datatype": doc["l2_datatype"],
                "value": doc["value"]
            }
            json_serializable_response.append(json_serializable_doc)


        logging.debug("Final response saved successfully")


        return JSONResponse(content=json_serializable_response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/generativeaisrvc/map_fields_to_policy/")
async def map_fields_to_policy(payload: Dict[str, Any]):
    body = payload.get("body")
    policy_mapping = payload.get("policyMapping")

    if not body or not policy_mapping:
        raise HTTPException(status_code=400, detail="Body and policyMapping are required in the payload")

    mapped_data = {}

    for field, value in body.items():
        if isinstance(value, dict):
            # If the value is a dictionary (nested object), map its nested fields
            mapped_data[field] = map_nested_fields_to_policy(value, policy_mapping)
        else:
            # Map non-nested fields
            mapped_field, placeholder = map_field_to_policy(field, policy_mapping)
            if placeholder is not None:
                mapped_data[field] = placeholder
            else:
                mapped_data[field] = value

    return mapped_data


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
