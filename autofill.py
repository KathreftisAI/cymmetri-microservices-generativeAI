import uvicorn
from fastapi import FastAPI, Form, Request, HTTPException, Header, Response, status
import httpx
import json
import logging
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

app = FastAPI()
 
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

def extract_user_data(response):
    try:
        logging.debug("Extracting the users from the nested json")
        user_data_list = []

        def is_user_data(obj):
            # Convert keys in the object to lowercase for case-insensitive comparison
            lower_case_obj_keys = {key.lower() for key in obj.keys()}
            # Define user data keys in lowercase
            user_keys = {'displayname', 'givenname', 'email', 'id', 'dateofbirth', 'mobile', 'firstname', 'name', 'password'}
            # Check if object contains at least one of the common user data keys, ignoring case
            return any(key in lower_case_obj_keys for key in user_keys)

        def traverse(obj, original_keys=None):
            # Recursively traverse the JSON object
            if isinstance(obj, dict):
                if is_user_data(obj):
                    # Convert keys in the user data to lowercase or handle as needed
                    user_data_list.append({original_keys.get(k.lower(), k): v for k, v in obj.items()})
                else:
                    for key, value in obj.items():
                        # Maintain original keys for nested dictionaries
                        traverse(value, {**original_keys, **{key.lower(): key}})
            elif isinstance(obj, list):
                for item in obj:
                    traverse(item, original_keys)

        traverse(response, {})

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
    logging.debug(f"best match: {best_match}")
    logging.debug(f"score: {score}")
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


#-------------for badrequest---------
def create_bad_request_response(response_val):
    return Response(
        content=json.dumps(response_val),
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={'Content-Type': 'application/json'}
    )

def replace_values_with_placeholders(body, mapped_data):
    if isinstance(body, dict):
        for key, value in body.items():
            if key in mapped_data:
                body[key] = mapped_data[key]
            else:
                replace_values_with_placeholders(value, mapped_data)
    elif isinstance(body, list):
        for i, item in enumerate(body):
            if isinstance(item, dict) or isinstance(item, list):
                replace_values_with_placeholders(item, mapped_data)
    return body

#------- Api for body populating----------
# Modify the map_fields_to_policy endpoint if needed
@app.post("/generativeaisrvc/map_fields_to_policy")
async def map_fields_to_policy(payload: Dict[str, Any]):
    logging.debug(f"API call for auto fill policy for create/update user.")

    try:
        body = payload.get("body")
        policy_mapping = payload.get("policyMapping")

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

        json_data = extract_user_data(body)
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
        data = replace_values_with_placeholders(body, mapped_data)


        return data
        #return ResponseModel(data=data, message="Autofill executed successfully")


    except HTTPException:
        raise
    except Exception as e:
        return ErrorResponseModel(error=str(e), code=500, message="Exception while running autofill policy.", errorCode= "Invalid")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, debug=True)