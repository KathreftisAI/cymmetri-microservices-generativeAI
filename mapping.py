import requests
from pymongo import MongoClient

# Connect to MongoDB (replace the connection string with your actual MongoDB connection string)
mongo_connection_string = "mongodb://unoadmin:devDb123@10.0.1.6:27019,10.0.1.6:27020,10.0.1.6:27021/?authSource=admin&replicaSet=sso-rs&retryWrites=true&w=majority"
mongo_client = MongoClient(mongo_connection_string)

# Specify the database and collection from which you want to fetch data
mongo_db = mongo_client['darvin_user']
mongo_collection = mongo_db['new_user']

# Fetch JSON data from MongoDB
mongo_data = list(mongo_collection.find())

if len(mongo_data) > 0:
    sample_record = mongo_data[0]

    # Send the sample record to OpenAI for schema extraction
    openai_url = 'https://cymetriopen.openai.azure.com/openai/deployments/instructionalmodel/completions?api-version=2023-09-15-preview'
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

        # Extract only the text part from the OpenAI response
        response_text = openai_response.json()['choices'][0]['text']
        print(response_text)
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.RequestException as err:
        print(f"Request Exception: {err}")
else:
    print("No records found in the MongoDB collection.")
