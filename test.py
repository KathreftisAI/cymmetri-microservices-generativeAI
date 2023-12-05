import requests
from pymongo import MongoClient
import json

def fetch_sample_record(collection):
    data = list(collection.find())
    if len(data) > 0:
        return data[0]
    return None

# Connect to MongoDB for darvin_user.new_user collection
mongo_connection_string_darvin = "mongodb://unoadmin:devDb123@10.0.1.6:27019,10.0.1.6:27020,10.0.1.6:27021/?authSource=admin&replicaSet=sso-rs&retryWrites=true&w=majority"
mongo_client_darvin = MongoClient(mongo_connection_string_darvin)
mongo_db_darvin = mongo_client_darvin['darvin_user']
mongo_collection_darvin = mongo_db_darvin['new_user']

# Connect to MongoDB for bugfix-avi.user collection
# Connect to MongoDB for bugfix-avi.user collection
mongo_connection_string_bugfix = "mongodb://unoadmin:devDb123@10.0.1.6:27019,10.0.1.6:27020,10.0.1.6:27021/?authSource=admin&replicaSet=sso-rs&retryWrites=true&w=majority"
mongo_client_bugfix = MongoClient(mongo_connection_string_bugfix)
mongo_db_bugfix = mongo_client_bugfix['bugfix-avi']
mongo_collection_bugfix = mongo_db_bugfix['user']

# Fetch JSON data from darvin_user.new_user collection
sample_record_darvin = fetch_sample_record(mongo_collection_darvin)

if sample_record_darvin:
    # Send the sample record to OpenAI for schema extraction
    openai_url = 'https://cymetriopen.openai.azure.com/openai/deployments/instructionalmodel/completions?api-version=2023-09-15-preview'
    openai_headers = {
        'Content-Type': 'application/json',
        'api-key': 'ebe64320148849aead404cc3aec9cc49'
    }

    openai_payload = {
        "prompt": f"Give me list of fields as jsonPath and labels and datatype and value in this json sample {sample_record_darvin}",
        "max_tokens": 800,
        "temperature": 0.2,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "top_p": 1,
        "stop": None
    }

    try:
        openai_response = requests.post(openai_url, headers=openai_headers, json=openai_payload)
        openai_response.raise_for_status()

        # Extract only the text part from the OpenAI response
        openai_output = openai_response.json()['choices'][0]['text']

        # Extract labels from the OpenAI output
        openai_labels = [label.strip() for label in openai_output.split('\n') if label]

        # Fetch JSON data from bugfix-avi.user collection
        sample_record_bugfix = fetch_sample_record(mongo_collection_bugfix)

        if sample_record_bugfix:
            # Convert the JSON string to a dictionary
            sample_record_bugfix = json.loads(sample_record_bugfix)

            # Extract labels from the sample record in bugfix-avi.user
            bugfix_labels = [entry['label'] for entry in sample_record_bugfix]

            # Compare labels
            similar_labels = set(openai_labels).intersection(set(bugfix_labels))

            # Print similar labels
            print("Similar Labels:")
            print(similar_labels)
        else:
            print("No records found in bugfix-avi.user collection.")
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.RequestException as err:
        print(f"Request Exception: {err}")

else:
    print("No records found in the MongoDB collection.")
