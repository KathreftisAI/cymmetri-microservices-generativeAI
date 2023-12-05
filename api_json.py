import os
from fastapi import FastAPI, Form, HTTPException

import openai

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

def chat_with_bot(user_input):
    # Initialize the conversation with system and user messages
    conversation_history.append({"role": "user", "content": user_input})

    message_text = [
        {"role": "system", "content": "You are an AI assistant that helps people find information."},
        {"role": "user", "content": user_input},
    ] + conversation_history

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

    conversation_history.append({"role": "assistant", "content": response})
    stored_responses.append(response)  # Automatically store the response
    return response

# FastAPI endpoint for chatbot
@app.post("/chat")
def chat_endpoint(user_input: str = Form(...)):
    bot_reply = chat_with_bot(user_input)
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
