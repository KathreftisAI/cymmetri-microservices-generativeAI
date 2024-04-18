import csv
from pymongo import MongoClient
import json
from openai import OpenAI
import logging

client = OpenAI(api_key='ebe64320148849aead404cc3aec9cc49')


# Set up MongoDB connection
mongo_client = MongoClient("mongodb://unoadmin:devDb123@10.0.1.6:27019,10.0.1.6:27020,10.0.1.6:27021/?authSource=admin&replicaSet=sso-rs&retryWrites=true&w=majority")
db = mongo_client["cymmetri-development"]
collection = db["audit_log"]

logging.basicConfig(level=logging.DEBUG)


def extract_entities_from_description(description: str):
    return {"entities": [(0, len(description), "ENTITY")]}

def generate_training_data_with_prompt(description):
    openai_url = 'https://cymetriopen.openai.azure.com/openai/deployments/instructionalmodel/completions?api-version=2023-09-15-preview'
    openai_headers = {
        'Content-Type': 'application/json',
        'api-key': 'ebe64320148849aead404cc3aec9cc49'
    }

    openai_payload = {
        "prompt": f"Extract entities like USER_ID, ACTION, RESULT from the data: {description}",
        "max_tokens": 8000,
        "temperature": 0.2,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "top_p": 1,
        "stop": None
    }

    openai_response = client.completions.create(engine="text-davinci-003",
    prompt=json.dumps(openai_payload),
    headers=openai_headers)

    entities_response = openai_response.choices[0].text.strip()
    entities = extract_entities_from_description(entities_response)
    return entities

def process_data_in_batches_and_generate_training_set(batch_size=100):
    try:
        total_documents = collection.count_documents({})
        num_batches = (total_documents + batch_size - 1) // batch_size

        training_data = []

        for batch_num in range(num_batches):
            batch = list(collection.find().skip(batch_num * batch_size).limit(batch_size))
            for item in batch:
                description = item.get("description", "")
                entities = generate_training_data_with_prompt(description)
                training_data.append((description, entities))

            # Save each batch separately if needed
            save_to_csv(training_data, f"batch_{batch_num + 1}.csv")
            training_data = []

        # Save all data to a single CSV file
        save_to_csv(training_data, "all_data.csv")

        print("Processing completed successfully")
    except Exception as e:
        print(f"Error: {e}")

def save_to_csv(training_data, csv_file):
    with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["text", "entities"])
        for text, entities in training_data:
            csvwriter.writerow([text, json.dumps(entities)])

if __name__ == "__main__":
    process_data_in_batches_and_generate_training_set()
