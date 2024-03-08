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
from datetime import datetime
from dateutil.parser import parse
import json
from dateutil.parser import parse
import datetime
from datetime import date
from dateutil.parser import ParserError

app = FastAPI()
 

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(filename)s on %(lineno)d: %(message)s',
)

def stored_input(tenant: str):
    #logging.debug(f"Getting collection for tenant: {tenant}")
    return get_collection(tenant, "input")

def stored_response(tenant: str):
    #logging.debug(f"Getting collection for storing scores for tenant: {tenant}")
    return get_collection(tenant, "output")

def convert_string_to_list(input_str: str) -> List[str]:
    # Remove leading and trailing whitespaces, and split by ','
    return [element.strip() for element in input_str.strip('[]').split(',')]


def get_distinct_keys_and_datatypes(json_data):
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

#-----------------------------extracting the user object from response-----------------

def extract_user_data(response):
    user_data_list = []

    def is_user_data(obj):
        # Check if object contains at least one of the common user data keys
        user_keys = {'displayName', 'email', 'id', 'DateOfBirth'}
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

#----------------------api for policy mapping-----------------------------
@app.post('/generativeaisrvc/get_policy_mapped')
async def get_mapped(request: Request, data: dict):
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
                    #print(f"type of response {type(response)}")
                    #print("response: ",response)

        if response.status_code >= 200 or response.status_code <= 204:
            # Assuming the response contains JSON data, you can parse it
            json_data = response.json()
            json_data_ = extract_user_data(json_data)
            #print("json_data: ",json_data_)
            logging.debug(f"type of json_data is {type(json_data)}")

            response_data = get_distinct_keys_and_datatypes(json_data_)
            #return list(response_data.values())
            return response_data

        else:
            raise HTTPException(status_code=response.status_code, detail=f"API call to fetch data failed with status code {response.status_code}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)