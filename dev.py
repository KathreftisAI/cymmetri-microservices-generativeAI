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

#------------------- for creating dict---------------
synonyms_dict = {'department': {'division': 1, 'section': 1, 'unit': 1, 'branch': 1, 'sector': 1, 'departmentalunit': 1, 'team': 1, 'segment': 1, 'group': 1, 'subdivision': 1, 'area': 1, 'office': 1, 'bureau': 1, 'wing': 1, 'part': 1, 'component': 1, 'sphere': 1, 'category': 1, 'subunit': 1, 'subsection': 1}, 'employeeId': {'staffID': 1, 'workerID': 1, 'employeenumber': 1, 'identificationnumber': 1, 'personnelcode': 1, 'staffcode': 1, 'workercode': 1, 'employeereference': 1, 'staffreference': 1, 'personnelnumber': 1, 'employmentID': 1, 'jobID': 1, 'workID': 1, 'staffidentification': 1, 'staffreferencenumber': 1, 'employeeidentifier': 1, 'workeridentifier': 1, 'employmentnumber': 1, 'personnelID': 1, 'personnelidentifier': 1}, 'designation': {'title': 1, 'position': 1, 'role': 1, 'rank': 1, 'jobtitle': 1, 'function': 1, 'appointment': 1, 'capacity': 1, 'post': 1, 'task': 1, 'duty': 1, 'responsibility': 1, 'occupation': 1, 'roletitle': 1, 'positiontitle': 1, 'worktitle': 1, 'jobrole': 1, 'jobposition': 1, 'jobdesignation': 1, 'functiontitle': 1}, 'appUpdatedDate': {'applicationupdatedate': 1, 'softwareupdatedate': 1, 'appmodificationdate': 1, 'updatetimestamp': 1, 'softwarerevisiondate': 1, 'appupgradedate': 1, 'programupdatedate': 1, 'softwarerefreshdate': 1, 'appenhancementdate': 1, 'modificationtimestamp': 1, 'upgradetimestamp': 1, 'revisiontimestamp': 1, 'refreshtimestamp': 1, 'enhancementtimestamp': 1, 'softwarechangedate': 1, 'appchangedate': 1, 'changetimestamp': 1, 'updatetime': 1, 'modificationdate': 1, 'revisiondate': 1}, 'displayName': {'namedisplayed': 1, 'visiblename': 1, 'publicname': 1, 'nameshown': 1, 'presentationname': 1, 'exhibitedname': 1, 'publiclyshownname': 1, 'visibletitle': 1, 'exhibitedtitle': 1, 'publiclyshowntitle': 1, 'presentationtitle': 1, 'showntitle': 1, 'displayedtitle': 1, 'visibledesignation': 1, 'exhibiteddesignation': 1, 'publiclyshowndesignation': 1, 'presentationdesignation': 1, 'showndesignation': 1, 'displayeddesignation': 1, 'displayedidentity': 1}, 'mobile': {'cellular': 1, 'cellphone': 1, 'mobilephone': 1, 'wirelessphone': 1, 'portablephone': 1, 'handset': 1, 'smartphone': 1, 'cell': 1, 'mobiledevice': 1, 'mobilecellular': 1, 'portabledevice': 1, 'wirelessdevice': 1, 'cellulardevice': 1, 'handhelddevice': 1, 'cellularphone': 1, 'cellulartelephone': 1, 'mobileunit': 1, 'wirelessunit': 1}, 'country': {'nation': 1, 'state': 1, 'territory': 1, 'land': 1, 'countrystate': 1, 'nationstate': 1, 'realm': 1, 'region': 1, 'commonwealth': 1, 'province': 1, 'domain': 1, 'sovereignstate': 1, 'nationalterritory': 1, 'nationterritory': 1, 'countryterritory': 1, 'homeland': 1, 'fatherland': 1, 'motherland': 1, 'nativeland': 1, 'soil': 1}, 'city': {'metropolis': 1, 'urbancenter': 1, 'town': 1, 'municipality': 1, 'cityscape': 1, 'borough': 1, 'locality': 1, 'urbanarea': 1, 'downtown': 1, 'community': 1, 'village': 1, 'conurbation': 1, 'township': 1, 'megalopolis': 1, 'cosmopolis': 1, 'megalopolitanarea': 1, 'metropolitanarea': 1, 'megalopolitanregion': 1, 'citycenter': 1, 'citydistrict': 1}, 'email': {'electronicmail': 1, 'emailaddress': 1, 'e-message': 1, 'emailcorrespondence': 1, 'digitalmail': 1, 'e-mail': 1, 'internetmail': 1, 'onlinemail': 1, 'electroniccorrespondence': 1, 'cybermail': 1, 'virtualmail': 1, 'webmail': 1, 'internetmessage': 1, 'e-post': 1, 'e-letter': 1, 'electronicmessage': 1, 'e-communique': 1, 'digitalmessage': 1, 'onlinemessage': 1, 'webmessage': 1}, 'end_date': {'enddate': 1, 'terminationdate': 1, 'conclusiondate': 1, 'finishdate': 1, 'completiondate': 1, 'closingdate': 1, 'expirationdate': 1, 'finaldate': 1, 'culminationdate': 1, 'endingdate': 1, 'expirydate': 1, 'concludingdate': 1, 'ceasingdate': 1, 'lastdate': 1, 'terminationtime': 1, 'conclusiontime': 1, 'finishtime': 1, 'completiontime': 1, 'closingtime': 1, 'expirationtime': 1}, 'firstName': {'givenname': 1, 'forename': 1, 'firstname': 1, 'Christianname': 1, 'personalname': 1, 'individualname': 1, 'giventitle': 1, 'initialname': 1, 'name': 1, 'givenappellation': 1, 'appellation': 1, 'nametag': 1, 'namelabel': 1, 'givendesignation': 1, 'givenidentity': 1, 'title': 1, 'handle': 1, 'moniker': 1, 'nickname': 1, 'nomenclature': 1}, 'login': {'userprincipalname': 1, 'sign-in': 1, 'logon': 1, 'logincredentials': 1, 'access': 1, 'accesscode': 1, 'username': 1, 'userID': 1, 'loginID': 1, 'logonID': 1, 'sign-in details': 1, 'accessdetails': 1, 'accessinformation': 1, 'sign-ininformation': 1, 'logoninformation': 1, 'credentials': 1, 'authentication': 1, 'loginname': 1, 'sign-inname': 1, 'logonname': 1, 'accessname': 1}, 'lastName': {'familyname': 1, 'surname': 1, 'lastname': 1, 'secondname': 1, 'patronymic': 1, 'matronymic': 1, 'sirename': 1, 'maidenname': 1, 'maidensurname': 1, 'parentalname': 1, 'parentalsurname': 1, 'cognomen': 1, 'familytitle': 1, 'familyappellation': 1, 'familylabel': 1, 'familydesignation': 1, 'familyidentity': 1, 'familyhandle': 1}, 'userType': {'roletype': 1, 'usercategory': 1, 'accounttype': 1, 'userrole': 1, 'profiletype': 1, 'identitytype': 1, 'classification': 1, 'userclassification': 1, 'rolecategory': 1, 'userclass': 1, 'identityclass': 1, 'profileclass': 1, 'usergroup': 1, 'identitygroup': 1, 'profilegroup': 1, 'roleclassification': 1, 'userroleclassification': 1, 'identityroleclassification': 1, 'profileroleclassification': 1, 'useridentitytype': 1}, 'dateOfBirth': {'birthdate': 1, 'DOB': 1, 'dateofbirth': 1, 'natalday': 1, 'bornday': 1, 'anniversaryofbirth': 1, 'nativitydate': 1, 'birthday': 1, 'borndate': 1, 'nataldate': 1, 'anniversaryofnativity': 1, 'natalanniversary': 1, 'bornanniversary': 1, 'birthanniversary': 1, 'nativityday': 1, 'birthdayanniversary': 1}, 'endDate': {'enddate': 1, 'conclusiondate': 1, 'terminationdate': 1, 'finishdate': 1, 'completiondate': 1, 'closingdate': 1, 'expirationdate': 1, 'finaldate': 1, 'culminationdate': 1, 'endingdate': 1, 'expirydate': 1, 'concludingdate': 1, 'ceasingdate': 1, 'lastdate': 1, 'terminationtime': 1, 'conclusiontime': 1, 'finishtime': 1, 'completiontime': 1, 'closingtime': 1, 'expirationtime': 1}, 'startDate': {'startdate': 1, 'commencementdate': 1, 'beginningdate': 1, 'initiationdate': 1, 'commencingdate': 1, 'onsetdate': 1, 'commencementtime': 1, 'initiationtime': 1, 'starttime': 1, 'commencingtime': 1, 'onsettime': 1, 'commencementpoint': 1, 'initiationpoint': 1, 'startingpoint': 1, 'commencingpoint': 1, 'onsetpoint': 1, 'launchdate': 1, 'kickoffdate': 1, 'openingdate': 1, 'inaugurationdate': 1}, 'password': {'passcode': 1, 'accesscode': 1, 'securitycode': 1, 'logincode': 1, 'passphrase': 1, 'authenticationcode': 1, 'key': 1, 'secretkey': 1, 'code': 1, 'PIN': 1, 'loginkey': 1, 'accesskey': 1, 'passkey': 1, 'securitykey': 1, 'identificationcode': 1, 'authenticationkey': 1, 'cipher': 1, 'loginpassword': 1, 'securitypassword': 1, 'accesspassword': 1}, 'status': {'condition': 1, 'state': 1, 'situation': 1, 'standing': 1, 'position': 1, 'circumstance': 1, 'statusquo': 1, 'mode': 1, 'stage': 1, 'phase': 1, 'stateofaffairs': 1, 'positioning': 1, 'conditioning': 1, 'stateofbeing': 1, 'statuscondition': 1, 'statusstate': 1, 'statussituation': 1, 'statusposition': 1, 'statuscircumstance': 1, 'statusphase': 1}, 'profilePicture': {'avatar': 1, 'userimage': 1, 'displaypicture': 1, 'profileimage': 1, 'profilephoto': 1, 'userphoto': 1, 'portrait': 1, 'icon': 1, 'thumbnail': 1, 'representation': 1, 'graphic': 1, 'digitalimage': 1, 'visualrepresentation': 1, 'picture': 1, 'photo': 1, 'displayimage': 1, 'profileavatar': 1, 'useravatar': 1, 'image': 1, 'profilerepresentation': 1}, 'appUserId': {'applicationuserID': 1, 'softwareuseridentifier': 1, 'appaccountID': 1, 'userID': 1, 'accountID': 1, 'useridentity': 1, 'usercode': 1, 'useridentifier': 1, 'appidentity': 1, 'softwareID': 1, 'softwareidentifier': 1, 'applicationID': 1, 'applicationidentifier': 1, 'appcode': 1, 'softwarecode': 1, 'accountcode': 1, 'usernumber': 1, 'identitynumber': 1, 'IDcode': 1, 'IDnumber': 1}, 'landline': {'fixedline': 1, 'homephone': 1, 'landlinephone': 1, 'landlinenumber': 1, 'homephonenumber': 1, 'residencephone': 1, 'residenceline': 1, 'telephonenumber': 1, 'fixedphone': 1, 'fixedtelephone': 1, 'domesticphone': 1, 'domesticline': 1, 'domestictelphone': 1, 'housephone': 1, 'houseline': 1, 'housetelephone': 1, 'wiredphone': 1, 'wiredline': 1, 'wiredtelephone': 1, 'cordedphone': 1}}

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
    return get_collection(tenant, "schema_maker_input")

#--------------stored policymap for all users----------------
def stored_response(tenant: str):
    return get_collection(tenant, "schema_maker_final_output")

#------------subset policy map response--------------
def stored_policy_mapped(tenant: str):
    return get_collection(tenant, "schema_maker_policyMap")

#---------synonyms_dict for training--------
def retreive_synonyms(tenant: str):
    return get_collection(tenant, "synonyms_dict")

#------final policymap by admin for training purpose---------
def stored_admin_policymap(tenant: str):
    return get_collection(tenant, "schema_maker_final_policyMap")

#----------custom attributes for appending in cymmetri list-----
def retreive_custom_attributes(tenant: str):
    return get_collection(tenant, "custome_attribute_master")

#----------update the synonyms_dict by retraining------------
def stored_synonyms_dict(tenant: str, appId: str, synonyms_dict: dict):
    synonyms_collection = get_collection(tenant, "synonyms_dict")

    # Construct the document to be inserted or updated
    document = {
        "appId": appId,
        "synonyms": {key: [{"synonym": synonym, "score": synonyms_dict[key][synonym]} for synonym in synonyms_dict[key]] for key in synonyms_dict}
    }

    # Update the document in the collection
    synonyms_collection.update_one(
        {"appId": appId},
        {"$set": document},
        upsert=True  # This will insert the document if it doesn't exist
    )
    logging.debug("synonyms dict collection updated/created successfully")

    return synonyms_collection

#----------- score for confidence level
def stored_score(tenant: str, appId: str):
    score_collection = get_collection(tenant, "schema_maker_score")

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

#--------generate request_id-----------
def generate_request_id():
    id = uuid.uuid1()
    return id.hex

#--------------for adding custome attributes in cymmetri field list------------
def add_custom_attributes_to_list(l2, l2_datatypes, tenant):
    
    attribute_collection = retreive_custom_attributes(tenant)
    
    # Query to fetch custom attributes
    query_result = attribute_collection.find({"attributeType": "USER", "status": True})

    logging.debug("query executed succesfully")

    # Loop through the query results
    for result in query_result:
        # Get the 'name' field from the query result
        custom_attribute_name = result['name']

        # Get the 'provAttributeType' field from the query result
        custom_attribute_type = result['provAttributeType']

        # Append custom attribute name to l2 if it's not already in the list
        if custom_attribute_name not in l2:
            l2.append(custom_attribute_name)

        # Add custom attribute to l2_datatypes
        l2_datatypes[custom_attribute_name] = custom_attribute_type

    return l2, l2_datatypes

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
                            "label": key,
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
def compare_lists_with_fuzzy(l1, l2, threshold, synonyms_collection, appId):
    matching_elements_l1 = []
    matching_elements_l2 = []
    non_matching_elements_l1 = []
    non_matching_elements_l2 = []
 
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

        # If no match is found in the original list, check synonyms
        if not matching_element_l2:
            synonyms_doc = synonyms_collection.find_one({"appId": appId})
            if synonyms_doc:
                synonyms = synonyms_doc.get("synonyms", {})
                for key, values in synonyms.items():
                    for synonym_obj in values:
                        synonym = synonym_obj.get("synonym", "").lower()
                        score = synonym_obj.get("score", 0)
                        adjusted_score = score * 100
                        if el1 == synonym and adjusted_score >= threshold:
                            matching_element_l2 = key
                            max_similarity = adjusted_score  # Use score as similarity percentage
                            is_synonym_match = True
                            break
                    if is_synonym_match:
                        break
            
        if matching_element_l2:
            matching_elements_l1.append(element_l1.strip("'"))
            matching_elements_l2.append(matching_element_l2.strip("'"))
            if is_synonym_match:
                print(f"Match found for '{element_l1}' with synonym '{matching_element_l2}' (Score: {max_similarity})")
            else:
                print(f"Match found for '{element_l1}' with '{matching_element_l2}' (Similarity: {max_similarity})")
        else:
            non_matching_elements_l1.append(element_l1.strip("'"))
 
    non_matching_elements_l2 = [
        element_l2.strip("'")
        for element_l2 in l2
        if element_l2.strip("'") not in matching_elements_l2
    ]
 
    similar_elements = []
    for element_l1, element_l2 in zip(matching_elements_l1, matching_elements_l2):
        similarity_percentage = fuzz.ratio(element_l1.lower(), element_l2.lower()) / 100
        matching_condition = "Fuzzy"
        similar_elements.append({
            "element_name_l1": element_l1,
            "element_name_l2": element_l2,
            "similarity_percentage": similarity_percentage,
            "matching_condition": matching_condition  # Adding matching condition to the result
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
                    'confidence': confidence,  # Include confidence level
                    'matching_condition': element["matching_condition"]
                })
                processed_labels.add(element['element_name_l1'])  # Track processed labels
        else:
            print(f"No matched data found for {element['element_name_l1']}")

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
                'confidence': confidence,  # Include confidence level
                "matching_condition": ""
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
    print("Headers:", tenant)
    logging.debug(f"API call for auto policy mapping with the application")
    try:
        
        input_collection =  stored_input(tenant)
        output_collection =  stored_response(tenant)
        subset_collection = stored_policy_mapped(tenant)
        synonyms_collection = retreive_synonyms(tenant)
        
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
                        'login': 'STRING',
                        'lastName': 'STRING',
                        'userType': 'STRING',
                        'end_date': 'DATE',
                        'login': 'STRING    ',
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
        
        l2, l2_datatypes = add_custom_attributes_to_list(l2, l2_datatypes, tenant)

        print("list2: ",l2)
        
        if isinstance(l2, str):
            l2_list = convert_string_to_list(l2)
        else:
            l2_list = l2

        threshold = 60
        appId = data.get("appId")

        synonyms_stored_collection = stored_synonyms_dict(tenant, appId, synonyms_dict)

        result = compare_lists_with_fuzzy(l1_list, l2_list, threshold, synonyms_collection, appId)
        print("result: ",result)

        request_id = generate_request_id()
   
        score_collection = stored_score(tenant, appId)

        final_response = generate_final_response(result['similar_elements'], response_data, l2_datatypes, score_collection)
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
                "matching_condition": "$data.matching_condition"
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
                "matching_condition": doc["matching_condition"]
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
    
#------- Api for body populating----------
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
    

#-------------------Api fpr storing the admin final policymap for training purpose-----------
@app.post("/generativeaisrvc/store_data")
async def store_data(payload: dict, tenant: str = Header(None)):
    try:
        policymap_colection = stored_admin_policymap(tenant)
        policymap_colection.insert_one(payload) 
        return {"message": "Data saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)