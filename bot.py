import os
from fastapi import FastAPI, Form, HTTPException
import openai
import json
 
openai.api_type = "azure"
openai.api_base = "https://cymetriopen.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = "ebe64320148849aead404cc3aec9cc49"
 
app = FastAPI()
 
# Maintain conversation history
conversation_history = []
stored_responses = []
 
# Load or initialize the seed from a file
seed_file = "seed.txt"
if os.path.exists(seed_file):
    with open(seed_file, "r") as file:
        seed = int(file.read())
else:
    seed = 42  # Set a default seed if the file doesn't exist
 
def get_response_text(response):
    try:
        # Attempt to get the text content from the response
        text_content = response['choices'][0]['message']['content']
        return text_content
    except (KeyError, IndexError):
        return None
 
def format_mapped_elements(response):
    mapped_elements = []
    try:
        # Extracting the mapped elements from the string process
        start_index = response.find("{")
        end_index = response.rfind("}")
        json_content = response[start_index:end_index + 1]
        json_data = json.loads(json_content)
 
        for key, value in json_data.items():
            mapped_elements.append({"l1 element": key, "l2 element": value})
        return mapped_elements
    except (KeyError, ValueError):
        return None
 
def chat_with_bot(l1, l2, syntax):
    while True:
        # Concatenate l1, l2, and syntax into a single input string
        input_text = f"{l1}\n{l2}\n{syntax}"
 
        # Initialize the conversation with system messages
        message_text = [
            {"role": "system", "content": "You are an AI assistant that helps people find information."},
        ]
 
        # Append user inputs to the conversation
        message_text.append({"role": "user", "content": input_text})
 
        # Call OpenAI to get a response
        completion = openai.ChatCompletion.create(
            engine="tesrt",
            messages=message_text,
            temperature=0.8,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            seed=seed  # Use the seed value
        )
 
        # Get the assistant's response
        response = get_response_text(completion)
        print("Response received from OpenAI:", response)
 
        # Format the mapped elements from the response
        formatted_elements = format_mapped_elements(response)
 
        conversation_history.append({"role": "assistant", "content": formatted_elements})
        stored_responses.append(formatted_elements)  # Automatically store the response
 
        return formatted_elements
 
 
# FastAPI endpoint for comparison and filtering
@app.post("/compare")
def compare_elements(l1: str = Form(...), l2: str = Form(...), syntax: str = Form(...)):
    # Fetch the complete element names from the original chat response
    chat_response = chat_with_bot(l1, l2, syntax)
   
    # Extract complete element names for l1 and l2
    matching_elements = [
        {"l1": element["l2 element"]["l1"], "l2": element["l2 element"]["l2"]}
        for element in chat_response
    ]
   
    return {"matching_elements": matching_elements}
 
 
 
# Run the FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
 
# Save the seed for the next run
with open(seed_file, "w") as file:
    file.write(str(seed))