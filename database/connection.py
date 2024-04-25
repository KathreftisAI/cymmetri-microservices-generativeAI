import os
from pymongo import MongoClient
from config.loader import Configuration
import platform
import logging
from fastapi import FastAPI, Form, Request, HTTPException, Header
 
def load_configuration():
    if platform.system() == 'Darwin':
        c = Configuration(r"config.yaml")
    else:
        c = Configuration("/config/config.yaml")

    return c.getConfiguration()
 
data = load_configuration()
 
MONGO_DETAILS = data["MONGODB_CONNECTION_STRING"]
BASE_TENANT_STRING = data["CYMMETRI_DB_PREFIX"] + "%s"
mongo_client = MongoClient(MONGO_DETAILS)
 
def get_collection(tenant_name: str, collection_name: str):
    try:
        mongo_tenant_details = BASE_TENANT_STRING % tenant_name
        database = mongo_client[mongo_tenant_details]
        generic_collection = database[collection_name]
        return generic_collection
    except Exception as e:
        raise HTTPException(status_code=400, detail="MONGODB_CONNECTION_ERROR")


# TODO: read from prefix and remove -
def get_master_collection(collection_name: str):
    try:
        master_db_name = data["CYMMETRI_DB_PREFIX"].split("-")[0]
        database = mongo_client[master_db_name]
        master_collection = database[collection_name]
        return master_collection
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))  # Providing exception details for better debugging