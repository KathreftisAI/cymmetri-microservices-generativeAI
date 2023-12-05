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
        # Extracting the mapped elements from the string response
        start_index = response.find("{")
        end_index = response.rfind("}")
        json_content = response[start_index:end_index + 1]
        json_data = json.loads(json_content)
 
        for key, value in json_data.items():
            mapped_elements.append(f"{{\"l1 element\": \"{key}\", \"l2 element\": \"{value}\"}}")
 
        return mapped_elements
    except (KeyError, ValueError):
        return None
 
 
def chat_with_bot(l1, l2, syntax):
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
        stop=None
    )
 
    # Get the assistant's response
    response = get_response_text(completion)
    print("Response received from OpenAI:", response)
 
    # Format the mapped elements from the response
    formatted_elements = format_mapped_elements(response)
 
    conversation_history.append({"role": "assistant", "content": formatted_elements})
    stored_responses.append(formatted_elements)  # Automatically store the response
    return formatted_elements
 
# FastAPI endpoint for chatbot
@app.post("/chat")
def chat_endpoint(l1: str = Form(...), l2: str = Form(...), syntax: str = Form(...)):
    bot_reply = chat_with_bot(l1, l2, syntax)
    return {"bot_reply": bot_reply}
 
# FastAPI endpoint to get stored responses
@app.get("/get_responses")
def get_responses():
    if not stored_responses:
        raise HTTPException(status_code=404, detail="No stored responses")
    return {"stored_responses": stored_responses}
 
# Run the FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)