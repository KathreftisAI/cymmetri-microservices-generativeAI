import os
from fastapi import FastAPI, Form, HTTPException
import openai
import json
from fastapi.responses import HTMLResponse
 
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
   
 
def chat_with_bot(l1, l2, syntax):
    while True:
        # Concatenate l1, l2, and syntax into a single input string
        input_text = f"{l1}\n{l2}\n{syntax}"
 
        # Initialize the conversation with system messagess``
        message_text = [
            {"role": "system", "content": "You are an AI assistant that helps people find information."},
        ]
 
        # Append user inputs to the conversation
        message_text.append({"role": "user", "content": input_text})
 
        # Call OpenAI to get a response
        completion = openai.ChatCompletion.create(
            engine="tesrt",
            messages=message_text,
            temperature=0.5,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None
        )
        
 
        # Get the assistant's response
        response = get_response_text(completion)
        print("Response received from OpenAI:", response)
 
        try:
            response_dict = json.loads(response)
            similar_elements = response_dict.get("similar_elements", [])
        except (KeyError, ValueError):
            similar_elements = []


        # Update stored responses with extracted elements
        formatted_elements = format_mapped_elements(response)
        conversation_history.append({"role": "assistant", "content": formatted_elements})
        stored_responses.append({"content": formatted_elements, "similar_elements": similar_elements})

        return formatted_elements


#Route to serve the index.html file
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("sp.html", "r") as file:
        return file.read()


# FastAPI endpoint for chatbot
# @app.post("/chat")
# def chat_endpoint(l1: str = Form(...), l2: str = Form(...), syntax: str = Form(...)):
#     bot_reply = chat_with_bot(l1, l2, syntax)
#     return {"bot_reply": bot_reply}

@app.post("/chat")
def chat_endpoint(l1: str = Form(...), l2: str = Form(...), syntax: str = Form(...)):
    bot_reply = chat_with_bot(l1, l2, syntax)

    # Update response dictionary with default L2 values
    response_dict = {"bot_reply": bot_reply}
    stored_response = stored_responses[-1]
    for i, l1_element in enumerate(bot_reply):
        for similar_element in stored_response["similar_elements"]:
            if l1_element["l1 element"] == similar_element["l1_element"]:
                response_dict["bot_reply"][i]["l2 element"] = similar_element["l2_element"]
                break
    print("response_dict: ",response_dict)
    return response_dict
  
# Run the FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)