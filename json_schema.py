import requests

# Fetch JSON data from the specified URL
data_url = 'https://jsonplaceholder.typicode.com/users'
response = requests.get(data_url)

if response.status_code == 200:
    # Assuming the response contains JSON data, you can parse it
    json_data = response.json()

    if isinstance(json_data, list) and len(json_data) > 0:
        sample_record = json_data[0]

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
        print("No records found in the JSON data.")
else:
    print(f"API call to fetch data failed with status code {response.status_code}")
