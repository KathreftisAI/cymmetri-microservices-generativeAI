import requests
from pymongo import MongoClient

# Connect to your MongoDB database
mongo_client = MongoClient('mongodb://unoadmin:devDb123@10.0.1.6:27019,10.0.1.6:27020,10.0.1.6:27021/?authSource=admin&replicaSet=sso-rs&retryWrites=true&w=majority')
db = mongo_client['ds-research']
collection = db['slack_source_data']

# Fetch multiple records from the MongoDB collection
mongo_records = list(collection.find({}))

if mongo_records:
    sample_record = mongo_records[0]

    # Send the sample record to OpenAI for schema extraction
    openai_url = 'https://cymetriopen.openai.azure.com/openai/deployments/tesrt/completions?api-version=2023-09-15-preview'
    openai_headers = {
        'Content-Type': 'application/json',
        'api-key': 'ebe64320148849aead404cc3aec9cc49'
    }

    openai_payload = {
        "prompt": f"Give me list of fields as jsonPath and labels and datatype and value in this json sample {sample_record}",
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

        schema_data = openai_response.json()
        print(schema_data)
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.RequestException as err:
        print(f"Request Exception: {err}")
else:
    print("No records found in the MongoDB collection.")
    
