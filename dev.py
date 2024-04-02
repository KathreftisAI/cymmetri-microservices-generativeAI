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

#--------------for adding custome attributes in cymmetri field list------------
def add_custom_attributes_to_list(l2, l2_datatypes, tenant):

    attribute_collection = retrieve_custom_attributes(tenant)

    #query_result = attribute_collection.find({"attributeType": "USER", "status": True})
    query_result = attribute_collection.find({"attributeType": "USER", "status": True})

    
    logging.debug("query executed successfully")
    
    custom_attributes = []  # This will track the names of custom attributes added

    for result in query_result:
        custom_attribute_name = result['name']
        custom_attribute_type = result['provAttributeType']
        
        if custom_attribute_name not in l2:
            l2.append(custom_attribute_name)
            custom_attributes.append(custom_attribute_name)  # Add to custom_attributes set if it's new
        
        l2_datatypes[custom_attribute_name] = custom_attribute_type

    return l2, l2_datatypes, custom_attributes


#-----------------------------extracting the user object from response-----------------
def extract_user_data(response):
    try:
        logging.debug("Extracting the users from the nested json")
        user_data_list = []

        def is_user_data(obj):
            # Convert keys in the object to lowercase for case-insensitive comparison
            lower_case_obj_keys = {key.lower() for key in obj.keys()}
            # Define user data keys in lowercase
            user_keys = {'displayname', 'givenname', 'email', 'id', 'dateofbirth', 'mobile', 'firstname'}
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
    
#---------------------------extracting keys, datatype, label and jsonpath----------------
def get_distinct_keys_and_datatypes(json_data):
    try:
        logging.debug("Extracting the properties from the JSON data")
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
                        # Construct the label using parent keys if path is nested
                        "label": ".".join(new_path.split(".")[1:]) if "." in new_path else key,
                        "datatype": datatype,
                        "value": value
                    })
            elif isinstance(obj, list):
                if not obj:  # Check if the list is empty
                    datatype = 'ARRAY'
                    distinct_keys_datatypes.append({
                        "jsonpath": path,
                        "label": path.split('.')[-1],  # Get the key name from the path
                        "datatype": datatype,
                        "value": obj
                    })
                else:
                    for index, item in enumerate(obj):
                        new_path = f"{path}.{index}" if path else str(index)
                        if isinstance(item, dict) or isinstance(item, list):
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
                    parse_result = parse(value)
                    if (parse_result.strftime('%Y-%m-%d') == value) or (parse_result.strftime('%d-%m-%y') == value):
                        return 'DATE'
                    else:
                        if parse_result.time() != datetime.time(0, 0, 0):
                            return 'DATETIME'
                        else:
                            return 'STRING'
                except (ValueError, OverflowError):
                    return 'STRING'
            elif isinstance(value, bool):
                return 'BOOLEAN'
            elif isinstance(value, int):
                return 'INTEGER'
            elif isinstance(value, float):
                return 'FLOAT'
            elif isinstance(value, list):
                return 'ARRAY'
            elif value is None:
                return None
            else:
                return 'CUSTOM'

        explore_json(json_data)
        return distinct_keys_datatypes
    except Exception as e:
        raise HTTPException(status_code=400, detail="INVALID_JSON_DATA")
    

#-------------------fuzzy logic matching function----------------------
def compare_lists_with_fuzzy(l1, l2, threshold, synonyms_collection):
    matching_elements_l1 = []
    matching_elements_l2 = []
    non_matching_elements_l1 = []
    non_matching_elements_l2 = []
    similar_elements = []

    for element_l1 in l1:
        max_similarity = 0
        matching_element_l2 = ''
        is_synonym_match = False  # Flag to track if a synonym match is found

        # Check similarity with original list (l2)
        for element_l2 in l2:
            el1 = str(element_l1).lower()
            el2 = str(element_l2).lower()
            similarity = fuzz.ratio(el1, el2)
            if similarity > max_similarity and similarity >= threshold:
                max_similarity = similarity
                matching_element_l2 = element_l2

        if not matching_element_l2:
            synonyms_doc = synonyms_collection.find_one()
            if synonyms_doc:
                threshold_synonyms = threshold / 100
                data = synonyms_collection.aggregate([
                    {
                        "$project": {
                            "synonymsArray": {"$objectToArray": "$synonyms"}
                        }
                    },
                    {"$unwind": "$synonymsArray"},
                    {
                        "$match": {
                            "synonymsArray.v": {
                                "$elemMatch": {
                                    "synonym": el1,
                                    "score": {"$gt": threshold_synonyms}
                                }
                            }
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "key": "$synonymsArray.k",
                            "synonyms": {
                                "$filter": {
                                    "input": "$synonymsArray.v",
                                    "as": "syn",
                                    "cond": {
                                        "$and": [
                                            {"$eq": ["$$syn.synonym", el1]},
                                            {"$gt": ["$$syn.score", threshold_synonyms]}
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    {"$limit": 1}
                ])
                if data:
                    for document in data:
                        matching_element_l2 = document.get('key', None)
                        synonyms = document.get('synonyms', [])
                        max_similarity = None
                        if synonyms:
                            max_similarity = max(synonyms, key=lambda x: x.get('score', 0)).get('score', None)
                            is_synonym_match = True
                            break

                else:
                    matching_element_l2 = None
                    max_similarity = None

        if matching_element_l2:
            matching_elements_l1.append(element_l1.strip("'"))
            matching_elements_l2.append(matching_element_l2.strip("'"))
            if is_synonym_match:
                similar_elements.append({
                    "element_name_l1": element_l1,
                    "element_name_l2": matching_element_l2,
                    "similarity_percentage": max_similarity,
                    "matching_decision": "synonyms"
                })
            else:
                similarity_percentage = fuzz.ratio(element_l1.lower(), matching_element_l2.lower()) / 100
                similar_elements.append({
                    "element_name_l1": element_l1,
                    "element_name_l2": matching_element_l2,
                    "similarity_percentage": similarity_percentage,
                    "matching_decision": "fuzzy"
                })
        else:
            non_matching_elements_l1.append(element_l1.strip("'"))

    non_matching_elements_l2 = [
        element_l2.strip("'")
        for element_l2 in l2
        if element_l2.strip("'") not in matching_elements_l2
    ]

    result = {
        "similar_elements": similar_elements
    }
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
            if similarity_score >= score_doc['HIGH'][0] and similarity_score <= score_doc['HIGH'][1]:
                return "HIGH"
            elif similarity_score >= score_doc['MEDIUM'][0] and similarity_score <= score_doc['MEDIUM'][1]:
                return "MEDIUM"
            elif similarity_score >= score_doc['LOW'][0] and similarity_score <= score_doc['LOW'][1]:
                return "LOW"
            else:
                return "Unknown"  # Should not happen if the schema is properly defined
        else:
            return "Unknown"  # No matching range found, return Unknown
    except Exception as e:
       raise HTTPException(status_code=400, detail="score_collection_error")


#----------------------generates final response---------------
def generate_final_response(similar_elements: List[Dict[str, Union[str, int, float]]], 
                            response_data: List[Dict[str, str]], 
                            l2_datatypes: Dict[str, str], 
                            score_collection,
                            custom_attributes: List[str]) -> List[Dict[str, Union[str, int, float]]]:
    logging.debug("Beautifying the response for saving into the collection")
    final_response = []

    processed_labels = set()
    
    for element in similar_elements:
        matched_data = [data for data in response_data if data['label'] == element['element_name_l1']]

        if matched_data:
            for match in matched_data:
                l2_datatype = l2_datatypes.get(element['element_name_l2'], None)
                confidence = get_confidence_level(element['similarity_percentage'], score_collection)
                
                # Determine if the attribute is custom based on the existence in the custom attributes set
                is_custom = element['element_name_l2'] in custom_attributes

                final_response.append({
                    'jsonPath': match['jsonpath'],
                    'attributeName': element['element_name_l1'],
                    'l1_datatype': match['datatype'],
                    'l2_matched': element['element_name_l2'],
                    'l2_datatype': l2_datatype,
                    'value': match['value'],
                    'similarity_percentage': element['similarity_percentage'],
                    'confidence': confidence,
                    'matching_decision': element["matching_decision"],
                    'isCustom': is_custom
                })
                processed_labels.add(element['element_name_l1'])
        else:
            logging.debug(f"No matched data found for {element['element_name_l1']}")


    for data in response_data:
        if data['label'] not in processed_labels:
            confidence = get_confidence_level(0, score_collection)
            final_response.append({
                'jsonPath': data['jsonpath'],
                'attributeName': data['label'],
                'l1_datatype': data['datatype'],
                'l2_matched': '',
                'l2_datatype': '',
                'value': data['value'],
                'similarity_percentage': 0,
                'confidence': confidence,
                'matching_decision': "",
                'isCustom': False  # Explicitly false since there's no l2 match
            })
    
    return final_response


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
    
    # Perform fuzzy matching if no direct match is found
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


#----------------------api for policy mapping-----------------------------
@app.post('/generativeaisrvc/get_policy_mapped')
async def get_mapped(data: dict, tenant: str = Header(...)):
    logging.debug(f"API call for auto policy mapping with the application")
    try:

        synonyms_collection = get_master_collection("amayaSynonymsMaster")
        input_collection =  stored_input(tenant)
        output_collection =  stored_response(tenant)
        subset_collection = stored_policy_mapped(tenant)

        custom_attributes = []
        
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
            if isinstance(data['payload'], list):
                # Convert list of dictionaries to a single dictionary
                converted_payload = {}
                for item in data['payload']:
                    for key, value in item.items():
                        converted_payload[key] = value
                data['payload'] = converted_payload
            else:
                raise HTTPException(status_code=400, detail="'payload' must be a dictionary or list")        
 
        json_data = data.get('payload')

        #print("json data is {}", json_data)

        json_data_ = extract_user_data(json_data)

        if json_data_:
            logging.info(f" Successfully extract the json data from response")

            response_data = get_distinct_keys_and_datatypes(json_data_)
            #response_data=list(response_data.values())
            #print("response_data:", response_data)


            l1 = [item['label'] for item in response_data]

            if isinstance(l1, str):
                l1_list = set(convert_string_to_list(l1))
                logging.info(f"list1: {l1_list}")
            else:
                #l1_list = remove_underscores_from_set(l1)
                l1_list = set(l1)
                #l1_list = set(l1_list)
                logging.info(f"list1: {l1_list}")



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
                            'login': 'STRING',
                            'lastName': 'STRING',
                            'userType': 'STRING',
                            'end_date': 'DATE',
                            'login': 'STRING',
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
            
            l2, l2_datatypes, custom_attributes = add_custom_attributes_to_list(l2, l2_datatypes, tenant)

            logging.info(f"list 2: {l2}")

            #print("custom_attributes: ", custom_attributes)
            
            if isinstance(l2, str):
                l2_list = convert_string_to_list(l2)
            else:
                l2_list = l2

            threshold = 60
            appId = data.get("appId")

            result = compare_lists_with_fuzzy(l1_list, l2_list, threshold, synonyms_collection)
            #print("result: ", result)
            
            request_id = generate_request_id()
    
            score_collection = stored_score(tenant, appId)

            final_response = generate_final_response(result['similar_elements'], response_data, l2_datatypes, score_collection, custom_attributes)
            #print("final response: ",final_response)
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
                    "confidence": "$data.confidence",
                    "matching_decision": "$data.matching_decision",
                    "isCustom": "$data.isCustom"
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
                    "confidence": doc["confidence"],
                    "matching_decision": doc["matching_decision"],
                    "isCustom": doc["isCustom"]
                }
                json_serializable_response.append(json_serializable_doc)


            aggregated_data = {
                "appId": appId,
                "request_id": request_id,
                "policyMapList": subset_response_data
            }

            subset_collection.insert_one(aggregated_data)

            logging.debug("subset response saved successfully")

            data_response = {
            "request_id": request_id,
            "content": json_serializable_response
        }

            #return JSONResponse(content=json_serializable_response)
            return ResponseModel(data=data_response, message="Policy mapping generated successfully")
        
        else:
            logging.info(f" Failed to extract the data from the response")
    
    except HTTPException:
        raise 

    except Exception as e:
        return ErrorResponseModel(error=str(e), code=500, message="Exception while running policy mappping.")
    
#------- Api for body populating----------
@app.post("/generativeaisrvc/map_fields_to_policy")
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
    


#-------------------Api fpr storing the admin final policymap for training purpose-----------
@app.post("/generativeaisrvc/store_data")
async def store_data(payload: dict, tenant: str = Header(None)):
    try:
        # Check if 'request_id' and 'payload' are present in the request
        if 'request_Id' not in payload:
            raise HTTPException(status_code=400, detail="Missing 'request_Id' in request")
        elif 'payload' not in payload:
            raise HTTPException(status_code=400, detail="Missing 'payload' in request")
        
        request_Id = payload.get("request_id")
        policymap_collection = stored_admin_policymap(tenant)
        policymap_collection.insert_one(payload) 

        logging.debug(f"Data inserted succesfully for request_Id : {request_Id}")

        # query AI suggestion collection
        subset_collection = stored_policy_mapped(tenant)
        doc1 = subset_collection.find_one({"request_id":request_Id})

        # query admin collection
        doc2 = policymap_collection.find_one({"request_id":request_Id})

        #query global collection
        synonyms_collection = get_master_collection("amayaSynonymsMaster")

        if doc1 and doc2:
            # print("doc1: ",doc1)
            # print("doc2: ",doc2)
            for policy1, policy2 in zip(doc1["policyMapList"], doc2["policyMapList"]):
                # print("policy1: ",policy1)
                # print("policy2: ",policy2)
                
                if policy1.get("matching_decision") == "synonyms" and policy2.get("matching_decision") == "synonyms" and policy1.get("l2_matched") != policy2.get("l2_matched"):
                    logging.debug(f" checking and updating score where policy1(AI) and policy2(admin) are not equal")
                    #Fetching attributeName from doc1
                    attribute_name1 = policy1.get("attributeName").lower()
                    print("attribute_name of the application: ",attribute_name1)
                    
                    # Fetching l2_matched from doc1
                    l2_matched1 = policy1.get("l2_matched")
                    print("l2_matched suggested by AI: ",l2_matched1)
                    
                    # Finding the attribute in the global collection
                    pipeline = [
                        {
                            "$match": {
                                f"synonyms.{l2_matched1}.synonym": attribute_name1
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "synonyms": {
                                    "$filter": {
                                        "input": f"$synonyms.{l2_matched1}",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.synonym", attribute_name1] }
                                    }
                                }
                            }
                        },
                        {
                            "$unwind": "$synonyms"
                        }
                    ]

                    global_docs = synonyms_collection.aggregate(pipeline)

                    for global_doc in global_docs:
                        synonyms = global_doc.get("synonyms", {})
                        if synonyms:
                            # Accessing the score and updating it
                            score = global_doc['synonyms']['score']
                            new_score = score - 0.2
                            # Updating the global collection with the new score
                            synonyms_collection.update_one(
                                {
                                    f"synonyms.{l2_matched1}.synonym": str(attribute_name1)
                                },
                                {
                                    "$set": {
                                        f"synonyms.{l2_matched1}.$[elem].score": float(new_score)
                                    }
                                },
                                array_filters=[
                                    {
                                        "elem.synonym": str(attribute_name1)
                                    }
                                ],
                                upsert= True
                            )

                            logging.debug(f"Updated score for {attribute_name1} to {new_score} since the suggestion given was wrong by AI")
                        else:
                            logging.debug("No 'synonyms' found in the document.")

                    #----------------------for storing new synonyms against the admin l2matched---------------------
                    attribute_name2 = policy2.get("attributeName").lower()
                    print("attribute_name of the application: ",attribute_name2)
                    
                    # Fetching l2_matched from doc2
                    l2_matched2 = policy2.get("l2_matched")
                    print("l2_matched by admin: ",l2_matched2)

                    new_synonym = {
                        "synonym": attribute_name2,
                        "score": 1
                    }
                    synonyms_collection.update_one(
                        {},
                        {
                            "$addToSet": {
                                f"synonyms.{l2_matched2}": new_synonym
                            }
                        },
                        upsert=True
                    )

                    logging.debug(f"Inserted new synonym as suggested by admin: {new_synonym}")
                
                elif policy1.get("matching_decision") == "synonyms" and policy2.get("matching_decision") == "synonyms" and policy1.get("l2_matched") == policy2.get("l2_matched"):
                    logging.debug(f" checking and updating score where policy1(AI) and policy2(admin) are equal")
                    attribute_name = policy1.get("attributeName").lower()
                    print("attribute_name of the application: ",attribute_name)
                    
                    # Fetching l2_matched from doc1
                    l2_matched = policy1.get("l2_matched")
                    print("l2_matched suggested by AI: ", l2_matched)
                    
                    # Finding the attribute in the global collection
                    pipeline = [
                        {
                            "$match": {
                                f"synonyms.{l2_matched}.synonym": attribute_name
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "synonyms": {
                                    "$filter": {
                                        "input": f"$synonyms.{l2_matched}",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.synonym", attribute_name] }
                                    }
                                }
                            }
                        },
                        {
                            "$unwind": "$synonyms"
                        }
                    ]

                    global_docs = synonyms_collection.aggregate(pipeline)

                    for global_doc in global_docs:

                        synonyms = global_doc.get("synonyms", {})
                        if synonyms:

                            score = global_doc['synonyms']['score']

                            if score is not None and score == 1:
                                new_score = 1  # If the current score is already 1, keep it unchanged
                            else:
                                new_score = score + 0.2

                            # Updating the global collection with the new score
                            synonyms_collection.update_one(
                                {
                                    f"synonyms.{l2_matched}.synonym": str(attribute_name)
                                },
                                {
                                    "$set": {
                                        f"synonyms.{l2_matched}.$[elem].score": float(new_score)
                                    }
                                },
                                array_filters=[
                                    {
                                        "elem.synonym": str(attribute_name)
                                    }
                                ],
                                upsert= True
                            )

                            logging.debug(f"Updated score for {attribute_name} to {new_score} since the suggestion given was right by AI")
                        else:
                            logging.debug("No 'synonyms' found in the document.")

                elif policy1.get("matching_decision") == "" and policy2.get("matching_decision") == "" and policy2.get("l2_matched")!= "":
                    logging.debug(f" checking and updating where matching decision is empty string")
                    
                    attribute_name2 = policy2.get("attributeName").lower()
                    print("attribute_name of the application: ",attribute_name2)
                    
                    # Fetching l2_matched from doc2
                    l2_matched2 = policy2.get("l2_matched")
                    print("l2_matched by admin: ",l2_matched2)

                    new_synonym = {
                        "synonym": attribute_name2,
                        "score": 1
                    }
                    synonyms_collection.update_one(
                        {},
                        {
                            "$addToSet": {
                                f"synonyms.{l2_matched2}": new_synonym
                            }
                        },
                        upsert=True
                    )
                    logging.debug(f"Inserted new synonym: {new_synonym}")


                else:
                    logging.debug("no need to analyze and changed")

        #compare fields and make calculation to update the in global collection
        return {"message": "Data saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#------------ API for mapping roles-------------
# @app.post("/generativeaisrvc/map_fields_to_roles")
# async def map_fields_to_roles(payload: Dict[str, Any]):
#     try:
#         body = payload.get("body")
#         policy_mapping = payload.get("policyMapping")

#         if not body:
#             raise HTTPException(status_code=400, detail="body empty")
#         elif not policy_mapping:
#             raise HTTPException(status_code=400, detail="policy_mapping empty")
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         return ErrorResponseModel(error=str(e), code=500, message="Exception while running mapping field.")

 

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)