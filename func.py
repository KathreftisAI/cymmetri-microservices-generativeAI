import json
import openai

def extract_labels_from_record(record):
    labels = []
    if isinstance(record, dict):
        for key in record.keys():
            if isinstance(key, str):
                label_entry = key.replace("_", " ").title().strip()
                labels.append(label_entry)
    return labels

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
        #Extracting the mapped elelments from the string process
        start_index = response.find("{")
        end_index = response.rfind("}")
        json_content = response[start_index:end_index + 1]
        json_data = json.loads(json_content)
 
        for key,value in json_data.items():
            mapped_elements.append({"l1 element": key, "l2 element": value})
        return mapped_elements
    except (KeyError,ValueError):
        return None
    

# Maintain conversation history
conversation_history = []
stored_responses = []

def chat_with_bot(l1, l2, syntax,seed=None):
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
            temperature=0.7,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            seed=seed
        )
 
        # Get the assistant's response
        response = get_response_text(completion)
        print("Response received from OpenAI:", response)
 
        # Format the mapped elements from the response
        formatted_elements = format_mapped_elements(response)
 
        conversation_history.append({"role": "assistant", "content": formatted_elements})
        stored_responses.append(formatted_elements)  # Automatically store the response
        return formatted_elements