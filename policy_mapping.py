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
import uuid

app = FastAPI()
 
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(filename)s on %(lineno)d: %(message)s',
)

def ResponseModel(data, message, code=200, error_code=None):
    return {
        "data": data,
        "code": code,
        "message": message,
        "error_code": error_code
    }

def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}

def stored_input(tenant: str):
    return get_collection(tenant, "schema_maker_input")

def stored_response(tenant: str):
    return get_collection(tenant, "schema_maker_final_output")

def stored_policy_mapped(tenant: str):
    return get_collection(tenant, "schema_maker_policyMap")

def stored_score(tenant: str, appId: str):
    score_collection = get_collection(tenant, "schema_maker_score")

    # Check if index exists
    #index_exists = appId in score_collection.index_information()
    
    # If index doesn't exist, create it
    # if not index_exists:
    #     score_collection.create_index("appId", unique=True)
    confidence_levels = {
        "HIGH": [70, 100],
        "LOW": [0, 30],
        "MEDIUM": [31, 69]
    }
    # Update or insert a single document for the given appId with confidence levels as fields
    score_collection.update_one(
        {"appId": appId},
        {"$set": {level: values for level, values in confidence_levels.items()}},
        upsert=True
    )
    logging.debug("score collection updated/created successfully")
    
    return score_collection

def convert_string_to_list(input_str: str) -> List[str]:
    # Remove leading and trailing whitespaces, and split by ','
    return [element.strip() for element in input_str.strip('[]').split(',')]

#--------generate request_id-----------
def generate_request_id():
    id = uuid.uuid1()
    return id.hex

#-----------------------------extracting the user object from response-----------------
def extract_user_data(response):
    try:
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
    except Exception as e:
        raise HTTPException(status_code=400, detail="INVALID_JSON_DATA")
    

#---------------------------extracting keys, datatype, label and jsonpath----------------

def get_distinct_keys_and_datatypes(json_data):
    try:
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
    except Exception as e:
       raise HTTPException(status_code=400, detail="INVALID_JSON_DATA")

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
            similarity = fuzz.ratio(el1, el2)
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
        similarity_percentage = fuzz.ratio(element_l1.lower(), element_l2.lower())
        similar_elements.append({
            "element_name_l1": element_l1,
            "element_name_l2": element_l2,
            "similarity_percentage": similarity_percentage
        })
 
    result = {"similar_elements": similar_elements}
    return result

#----------------------to get the confidence level based on schema_maker_score
def get_confidence_level(similarity_score: float, score_collection) -> str:
    try:
        # Query the collection to find the confidence level based on the similarity score
        score_doc = score_collection.find_one({
            "$or": [
                {"HIGH": {"$elemMatch": {"$gte": similarity_score}}},
                {"MEDIUM": {"$elemMatch": {"$gte": similarity_score}}},
                {"LOW": {"$elemMatch": {"$gte": similarity_score}}}
            ]
        })

        # Extract the confidence level based on the matched range
        if score_doc:
            if similarity_score >= score_doc['HIGH'][0]:
                return "HIGH"
            elif similarity_score >= score_doc['MEDIUM'][0]:
                return "MEDIUM"
            elif similarity_score >= score_doc['LOW'][0]:
                return "LOW"
            else:
                return "Unknown"  # Should not happen if the schema is properly defined
        else:
            return "Unknown"  # No matching range found, return Unknown
    except Exception as e:
       raise HTTPException(status_code=400, detail="score_collection_error")


#----------------------generates final response---------------
def generate_final_response(similar_elements: List[Dict[str, Union[str, int]]], response_data: List[Dict[str, str]], l2_datatypes: Dict[str, str], score_collection) -> List[Dict[str, Union[str, int, float]]]:
    logging.debug(f"Beautifying the response for saving into the collection")
    final_response = []
    processed_labels = set()
    
    # Create a dictionary for easy lookup of response_data based on labels
    response_lookup = {data['label']: data for data in response_data}
    for element in similar_elements:
        matched_data = [data for data in response_data if data['label'] == element['element_name_l1']]

        if matched_data:
            for match in matched_data:
                l2_datatype = l2_datatypes.get(element['element_name_l2'], None)
                # Query the schema_maker_score collection to get the confidence level
                confidence = get_confidence_level(element['similarity_percentage'], score_collection)
                final_response.append({
                    'jsonPath': match['jsonpath'],
                    'attributeName': element['element_name_l1'],
                    'l1_datatype': match['datatype'],
                    'l2_matched': element['element_name_l2'],
                    'l2_datatype': l2_datatype,
                    'value': match['value'],
                    'similarity_percentage': element['similarity_percentage'],
                    'confidence': confidence  # Include confidence level
                })
                processed_labels.add(element['element_name_l1'])  # Track processed labels
        else:
            print(f"No matched data found for {element['element_name_l1']}")

    print("processed_labels: ",processed_labels)

    # Handle unmatched elements from l1
    for data in response_data:
        if data['label'] not in processed_labels:
            # Query the schema_maker_score collection to get the confidence level
            confidence = get_confidence_level(0,score_collection)  # Default to 0 for unmatched elements
            final_response.append({
                'jsonPath': data['jsonpath'],
                'attributeName': data['label'],
                'l1_datatype': data['datatype'],
                'l2_matched': '',  # No match from l2
                'l2_datatype': '',
                'value': data['value'],  # Use value from response_data
                'similarity_percentage': 0,  # Default to 0 for unmatched elements
                'confidence': confidence  # Include confidence level
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
        subset_collection = stored_policy_mapped(tenant)

        # Store the received response directly into the input collection
        #input_collection.insert_one(data)

        #logging.debug("Input respone saved successfully")

        # Check if 'appId' and 'payload' are present in the request
        if 'appId' not in data:
            raise HTTPException(status_code=400, detail="Missing 'appId' in request")
        elif 'payload' not in data:
            raise HTTPException(status_code=400, detail="Missing 'payload' in request")

        # Validate the format of 'payload'
        if not isinstance(data['payload'], dict):
            raise HTTPException(status_code=400, detail="'payload' must be a dictionary")
        
 
        json_data = data.get('payload')

        #print("json data is {}", json_data)
        #End of changes by Abhishek

        json_data_ = extract_user_data(json_data)
        #print("json_data: ",json_data_)

        response_data = get_distinct_keys_and_datatypes(json_data_)
        #response_data=list(response_data.values())
        #print("response_data:", response_data)


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
        #print("result: ",result)

        appId = data.get("appId")

        request_id = generate_request_id()

        
        score_collection = stored_score(tenant, appId)

        final_response = generate_final_response(result['similar_elements'], response_data, l2_datatypes, score_collection)
        final_response_dict = {"final_response": final_response}

        # Assuming 'appId' is present in the received response
        final_response_dict['appId'] = appId

        output_collection.update_one(
            {"appId": appId},
            {"$set": final_response_dict},
            upsert=True
        )

        logging.debug("Final response saved successfully")

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
                "value": doc["value"],
                "similarity_percentage": doc["similarity_percentage"],
                "confidence": doc["confidence"]
            }
            json_serializable_response.append(json_serializable_doc)


        aggregated_data = {
            "appId": appId,
            "request_id": request_id,
            "subset_data": subset_response_data
        }

        subset_collection.insert_one(aggregated_data)

        logging.debug("subset response saved successfully")

        data_response = {
        "request_id": request_id,
        "content": json_serializable_response
    }

        #return JSONResponse(content=json_serializable_response)
        return ResponseModel(data=data_response, message="Policy mapping generated successfully")
    
    except HTTPException:
        raise 

    except Exception as e:
        return ErrorResponseModel(error=str(e), code=500, message="Exception while running policy mappping.")
    

@app.post("/generativeaisrvc/map_fields_to_policy/")
async def map_fields_to_policy(payload: Dict[str, Any]):
    try:
        body = payload.get("body")
        policy_mapping = payload.get("policyMapping")

        if not body:
            raise HTTPException(status_code=400, detail="body empty")
        elif not policy_mapping:
            raise HTTPException(status_code=400, detail="policy_mapping empty")

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
    
    except HTTPException:
        raise
    except Exception as e:
        return ErrorResponseModel(error=str(e), code=500, message="Exception while running mapping field.")
    
    
# @app.get('/query_requestor_id')
# async def query_requestor_id(requestor_id: str, tenant: str = Header(None)):
#     if not requestor_id:
#         raise HTTPException(status_code=400, detail="requestor_id missing")
    
#     subset_collection = stored_policy_mapped(tenant)
    
#     #Implement the policyMaptenant collection data coming from shivani
    

#     # Check if requestor_id is present in both collections
#     result1 = subset_collection.find_one({'requestor_id': requestor_id})
#     result2 = collection2.find_one({'requestor_id': requestor_id})

#     if result1 and result2:
#         return {"status": "ok"}
#     else:
#         raise HTTPException(status_code=404, detail="requestor_id not found")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)