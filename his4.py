# his2.py - Chatbot code

import openai
from fuzzywuzzy import fuzz

openai.api_type = "azure"
openai.api_base = "https://cymetriopen.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = "ebe64320148849aead404cc3aec9cc49"

# Maintain conversation history
conversation_history = []

def get_response_text(response):
    try:
        text_content = response['choices'][0]['message']['content']
        return text_content
    except (KeyError, IndexError):
        return None

def chat_with_bot(user_input):
    conversation_history.append({"role": "user", "content": user_input})

    message_text = [
        {"role": "system", "content": "You are an AI assistant that helps people find information."},
    ] + conversation_history

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

    response = get_response_text(completion)

    conversation_history.append({"role": "assistant", "content": response})

    return response

# Initial message
print("Chatbot: Hello! How can I assist you today?")

# Simulate an error in err.py
error_found = False
try:
    exec(open("java_err.java").read())
except Exception as e:
    error_message = str(e)
    print("error_msg: ", error_message)
    error_found = True
    # Use the error message as input for the chatbot
    #bot_reply = chat_with_bot(error_message)
    
    # If there is an error, fetch a solution from OpenAI
    openai_solution_prompt = f"Solve the error: {error_message}"
    openai_solution_response = chat_with_bot(openai_solution_prompt)
    print("bot: ",openai_solution_response)

if not error_found:
    print("No error found")

# Continue the conversation loop (optional)
while True:
    print("You: ")
    user_input = input()

    if user_input.lower() == 'exit':
        print("Chatbot: Goodbye!")
        break

    bot_reply = chat_with_bot(user_input)

    for message in reversed(conversation_history):
        if message["role"] == "assistant":
            similarity = fuzz.ratio(user_input.lower(), message["content"].lower())
            if similarity > 70:
                print(f"Chatbot: It seems like you've asked a similar question before. Here's a related response: {message['content']}")
                break
