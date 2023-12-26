import os
from pymongo import MongoClient
from config.loader import Configuration
import platform

def load_configuration():
    if platform.system() == 'Windows':
        c = Configuration("/Users/apple/Desktop/cymmetri/cymmetri-microservices-generativeAI/config.yaml")
    else:
        c = Configuration("config.yaml")
    return c.getConfiguration()

data = load_configuration()

MONGO_DETAILS = data["MONGODB_CONNECTION_STRING"]
BASE_TENANT_STRING = data["CYMMETRI_DB_PREFIX"] + "%s"
mongo_client = MongoClient(MONGO_DETAILS)

def get_collection(tenant_name: str, collection_name: str):
    mongo_tenant_details = BASE_TENANT_STRING % tenant_name
    database = mongo_client[mongo_tenant_details]
    generic_collection = database[collection_name]
    return generic_collection
