import uvicorn
from fastapi import FastAPI, Form, Request, HTTPException, Header
import httpx
import json
import logging
from fastapi import FastAPI, Form, Response, status
from fastapi.responses import JSONResponse
from fuzzywuzzy import fuzz
from typing import List, Union
import uvicorn
from typing import List, Dict, Union
from database.connection import get_collection, get_master_collection
from dateutil.parser import parse
from datetime import datetime
from datetime import date
import datetime
import json
from typing import Dict, Any, List
from fuzzywuzzy import process
import uvicorn
import uuid
from typing import Set
import re
from adding_syms import add_synonyms

app = FastAPI()

add_synonyms()
 
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(filename)s on %(lineno)d: %(message)s',
)


def ResponseModel(data, message, code=200, errorCode=None):
    return {
        "success": True,
        "data": data,
        "code": code,
        "message": message,
        "errorCode": errorCode
    }

def ErrorResponseModel(error, code, message, errorCode):
    return { 
        "data": None,
        "success": False,
        "code": code, 
        "message": message,
        "errorCode": errorCode,
        "error": error
        }

#--------- stored the payload as input----------
def stored_input(tenant: str):
    return get_collection(tenant, "amaya_input")

#--------------stored policymap for all users----------------
def stored_response(tenant: str):
    return get_collection(tenant, "amaya_final_output")

#------------subset policy map response--------------
def stored_policy_mapped(tenant: str):
    return get_collection(tenant, "amaya_policyMap")

#------final policymap by admin for training purpose---------
def stored_admin_policymap(tenant: str):
    return get_collection(tenant, "amaya_final_policyMap")

#----------custom attributes for appending in cymmetri list-----
def retrieve_custom_attributes(tenant: str):
    return get_collection(tenant, "custome_attribute_master")

#----------- score for confidence level
def stored_score(tenant: str, appId: str):
    score_collection = get_collection(tenant, "amaya_score")

    # Check if index exists
    #index_exists = appId in score_collection.index_information()
    
    # If index doesn't exist, create it
    # if not index_exists:
    #     score_collection.create_index("appId", unique=True)
    confidence_levels = {
        "HIGH": [0.7, 1],
        "LOW": [0, 0.3],
        "MEDIUM": [0.31, 0.69]
    }
    # Update or insert a single document for the given appId with confidence levels as fields
    score_collection.update_one(
        {"appId": appId},
        {"$set": {level: values for level, values in confidence_levels.items()}},
        upsert=True
    )
    logging.debug("score collection updated/created successfully")
    
    return score_collection

#------ for preprocess purpose-----------
def convert_string_to_list(input_str: str) -> List[str]:
    # Remove leading and trailing whitespaces, and split by ','
    return [element.strip() for element in input_str.strip('[]').split(',')]

#--------------for preprocess purpose
def remove_underscores_from_set(input_set):
    return set(element.replace('_', '') for element in input_set)

#--------generate request_id-----------
def generate_request_id():
    id = uuid.uuid1()
    return id.hex

#-------------for badrequest---------
def create_bad_request_response(response_val):
    return Response(
        content=json.dumps(response_val),
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={'Content-Type': 'application/json'}
    )


#-----------------------------extracting the user object from response-----------------
# def extract_user_data(response):
#     logging.debug(f"printing the parameter passed: {response}")
#     try:
#         logging.debug("Extracting the users from the nested json")
#         user_data_list = []

#         def is_user_data(obj):
#             logging.debug(f"going into is_user_data function")
#             # Convert keys in the object to lowercase for case-insensitive comparison
#             lower_case_obj_keys = {key.lower() for key in obj.keys()}
#             logging.debug(f"printing the lowe case obj: {lower_case_obj_keys}")
#             # Define user data keys in lowercase
#             user_keys = {'displayname', 'givenname', 'email', 'id', 'dateofbirth', 'mobile', 'firstname', 'name', 'password'}
#             # Check if object contains at least one of the common user data keys, ignoring case
#             return any(key in lower_case_obj_keys for key in user_keys)

#         def traverse(obj, original_keys=None):
#             logging.debug(f"going into this traverse function")
#             # Recursively traverse the JSON object
#             if isinstance(obj, dict):
#                 logging.debug(f"printing the dict passed : {dict}")
#                 if is_user_data(obj):
#                     # Convert keys in the user data to lowercase or handle as needed
#                     user_data_list.append({original_keys.get(k.lower(), k): v for k, v in obj.items()})
#                 else:
#                     for key, value in obj.items():
#                         # Maintain original keys for nested dictionaries
#                         traverse(value, {**original_keys, **{key.lower(): key}})
#             elif isinstance(obj, list):
#                 logging.debug(f"printing the list passed: {list}")
#                 for item in obj:
#                     traverse(item, original_keys)

#         traverse(response, {})

#         logging.debug(f"printing the user data list: {user_data_list}")

#         return user_data_list
    
#     except Exception as e:
#         logging.error(f"Error extracting user data: {e}")  
#         raise HTTPException(status_code=400, detail="INVALID_JSON_DATA")
    

import logging
import re
from fastapi import HTTPException

def extract_user_data(response):
    logging.debug(f"printing the parameter passed: {response}")
    try:
        logging.debug("Extracting the users from the nested json")
        user_data_list = []

        def preprocess_key(key):
            # Remove special characters and convert to lowercase
            return re.sub(r'[\W_]+', '', key).lower()

        def is_user_data(obj):
            logging.debug(f"going into is_user_data function")
            # Convert keys in the object to preprocessed format for case-insensitive comparison
            preprocessed_obj_keys = {preprocess_key(key) for key in obj.keys()}
            logging.debug(f"printing the preprocessed obj keys: {preprocessed_obj_keys}")
            # Define user data keys in preprocessed format
            user_keys = {'displayname', 'givenname', 'email', 'id', 'dateofbirth', 'mobile', 'firstname', 'name', 'password'}
            # Check if object contains at least one of the common user data keys
            return any(key in preprocessed_obj_keys for key in user_keys)

        def traverse(obj, original_keys=None):
            logging.debug(f"going into this traverse function")
            # Recursively traverse the JSON object
            if isinstance(obj, dict):
                logging.debug(f"printing the dict passed: {obj}")
                if is_user_data(obj):
                    # Convert keys in the user data to lowercase or handle as needed
                    user_data_list.append({original_keys.get(preprocess_key(k), k): v for k, v in obj.items()})
                else:
                    for key, value in obj.items():
                        # Maintain original keys for nested dictionaries
                        traverse(value, {**original_keys, **{preprocess_key(key): key}})
            elif isinstance(obj, list):
                logging.debug(f"printing the list passed: {obj}")
                for item in obj:
                    traverse(item, original_keys)

        traverse(response, {})

        logging.debug(f"printing the user data list: {user_data_list}")

        return user_data_list
    
    except Exception as e:
        logging.error(f"Error extracting user data: {e}")  
        raise HTTPException(status_code=400, detail="INVALID_JSON_DATA")



#--------------- for mapping the body in body populating api------------------
def map_field_to_policy(field: str, policy_mapping: List[Dict[str, Any]]) -> str:
    matched = False
    # Perform case-insensitive exact match
    for map_entry in policy_mapping:
        external_field = map_entry["external"]
        internal_field = map_entry["internal"]
        if external_field.lower() == field.lower():
            matched = True
            logging.debug(f"Exact match found: '{field}' -> '{external_field}'")
            return external_field, f"${{{external_field}}}"  # Use placeholder syntax
    
    #Perform fuzzy matching if no direct match is found
    best_match, score = process.extractOne(field.lower(), [map_entry["internal"].lower() for map_entry in policy_mapping])
    if score >= 70:  # Adjust the threshold as needed
        for map_entry in policy_mapping:
            if map_entry["internal"].lower() == best_match:
                matched = True
                logging.debug(f"Fuzzy match found: '{field}' -> '{map_entry['external']}' (Best match: '{best_match}')")
                return map_entry['external'], f"${{{map_entry['external']}}}"  # Use placeholder syntax
    
    if not matched:
        logging.debug(f"No match found for '{field}'")
    return field, None  


#------- works on nested conditions also
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


def replace_values_with_placeholders(body, mapped_data):
    if isinstance(body, dict):
        for key, value in body.items():
            if key in mapped_data:
                # Check if the original type in body is a list
                if isinstance(value, list):
                    # Replace but check if mapped_data[key] is also a list
                    if isinstance(mapped_data[key], list):
                        body[key] = mapped_data[key]
                    else:
                        # Wrap non-list data from mapped_data in a list
                        body[key] = [mapped_data[key]]
                else:
                    # Direct replacement for other types
                    body[key] = mapped_data[key]
            else:
                # Recurse into nested structures
                replace_values_with_placeholders(value, mapped_data)
    elif isinstance(body, list):
        for i, item in enumerate(body):
            if isinstance(item, (dict, list)):
                replace_values_with_placeholders(item, mapped_data)

    return body


#------- Api for body populating----------
@app.post("/generativeaisrvc/map_fields_to_policy")
async def map_fields_to_policy(payload: Dict[str, Any]):
    logging.debug(f"API call for auto fill policy for create/update user.")

    try:
        body = payload.get("body")

        parsed_body = json.loads(payload["body"])

        payload["body"] = parsed_body

        policy_mapping = payload.get("policyMapping")

        logging.debug(f"printing body: {parsed_body}")
        if not body:
            response_val = {
                "data": None,
                "success": False,
                "errorCode": "BODY_MISSING_ERROR",
                "message": "Missing 'body' in request"
            }
            return create_bad_request_response(response_val)
        
        elif not policy_mapping:
            response_val = {
                "data": None,
                "success": False,
                "errorCode": "POLICY_MAPPING_MISSING_ERROR",
                "message": "Missing 'policy_mapping' in request"
            }
            return create_bad_request_response(response_val)

        json_data = extract_user_data(parsed_body)
        json_data = json.dumps(json_data)
        json_data_ = json.loads(json_data)

        mapped_data = {}

        for item in json_data_:
            for field, value in item.items():
                if isinstance(value, dict):
                    mapped_data[field] = map_nested_fields_to_policy(value, policy_mapping)
                else:
                    mapped_field, placeholder = map_field_to_policy(field, policy_mapping)
                    if placeholder is not None:
                        mapped_data[field] = placeholder
                    else:
                        mapped_data[field] = value

        print("mapped_data: ",mapped_data)
        data = replace_values_with_placeholders(parsed_body, mapped_data)


        #return data
        return ResponseModel(data=data, message="Autofill executed successfully")


    except HTTPException:
        raise
    except Exception as e:
        return ErrorResponseModel(error=str(e), code=500, message="Exception while running autofill policy.", errorCode= "Invalid")

        #raise HTTPException(status_code=500, detail=str(e)) 
        


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)