import requests
from pymongo import MongoClient

def extract_labels_from_record(record):
    
    labels = []
    if isinstance(record, dict):
        for key, value in record.items():
            label_entry = {
                "jsonPath": key,
                "label": key.replace("_", " ").title(),
                "dataType": type(value).__name__,
                "value": value
            }
            labels.append(label_entry["label"])
    return labels

# Connect to MongoDB for darvin_user.new_user collection
mongo_connection_string_darvin = "mongodb://unoadmin:devDb123@10.0.1.6:27019,10.0.1.6:27020,10.0.1.6:27021/?authSource=admin&replicaSet=sso-rs&retryWrites=true&w=majority"
mongo_client_darvin = MongoClient(mongo_connection_string_darvin)
mongo_db_darvin = mongo_client_darvin['darvin_user']
mongo_collection_darvin = mongo_db_darvin['new_user']

# Connect to MongoDB for bugfix-avi.user collection
mongo_connection_string_bugfix = "mongodb://unoadmin:devDb123@10.0.1.6:27019,10.0.1.6:27020,10.0.1.6:27021/?authSource=admin&replicaSet=sso-rs&retryWrites=true&w=majority"
mongo_client_bugfix = MongoClient(mongo_connection_string_bugfix)
mongo_db_bugfix = mongo_client_bugfix['bugfix-avi']
mongo_collection_bugfix = mongo_db_bugfix['user']

# Fetch JSON data from darvin_user.new_user collection
mongo_data_darvin = list(mongo_collection_darvin.find())

if len(mongo_data_darvin) > 0:
    sample_record_darvin = mongo_data_darvin[0]

    # Extract labels from the sample record in darvin_user.new_user
    labels_darvin = extract_labels_from_record(sample_record_darvin)

    # Print labels from darvin_user.new_user
    print("Labels from darvin_user.new_user:")
    print(labels_darvin)

    # Fetch JSON data from bugfix-avi.user collection
    mongo_data_bugfix = list(mongo_collection_bugfix.find())

    if len(mongo_data_bugfix) > 0:
        sample_record_bugfix = mongo_data_bugfix[0]

        # Extract labels from the sample record in bugfix-avi.user
        labels_bugfix = extract_labels_from_record(sample_record_bugfix)

        # Print labels from bugfix-avi.user
        print("Labels from bugfix-avi.user:")
        print(labels_bugfix)

        # Send labels to OpenAI for finding similar labels
        openai_url = 'https://cymetriopen.openai.azure.com/openai/deployments/instructionalmodel/completions?api-version=2023-09-15-preview'
        openai_headers = {
            'Content-Type': 'application/json',
            'api-key': 'ebe64320148849aead404cc3aec9cc49'
        }

        openai_payload = {
            "prompt": f"Find all labels in: {labels_darvin} and {labels_bugfix} and store in list name as l1 and l2",
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
            json_response_from_openai = openai_response.json()
            similar_labels = openai_response.json()['choices'][0]['text']
            print("Similar Labels:")
            print(similar_labels)


            #print("-=------------")
            #print(json_response_from_openai)
        except requests.exceptions.HTTPError as errh:
            print(f"HTTP Error: {errh}")
        except requests.exceptions.RequestException as err:
            print(f"Request Exception: {err}")

    else:
        print("No records found in bugfix-avi.user collection.")
else:
    print("No records found in darvin_user.new_user collection.")
