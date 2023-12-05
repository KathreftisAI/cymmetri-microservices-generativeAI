import os
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
        # Attempt to get the text content from the response
        text_content = response['choices'][0]['message']['content']
        return text_content
    except (KeyError, IndexError):
        return None

def chat_with_bot(user_input):
    # Append user message to conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Initialize the conversation with system and user messages
    message_text = [
        {"role": "system", "content": "You are an AI assistant that helps people find information."},
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

    # Print the assistant's response
    response = get_response_text(completion)
    print("Bot:", response)

    # Append bot message to conversation history
    conversation_history.append({"role": "assistant", "content": response})

    return response

# Initial message
print("Chatbot: Hello! How can I assist you today?")

# Chat loop
while True:
    # Get user input
    user_input = input("You: ")

    # Check if the user wants to exit the conversation
    if user_input.lower() == 'exit':
        print("Chatbot: Goodbye!")
        break

    # Generate response
    bot_reply = chat_with_bot(user_input)

    #use fuzzy logic to compare the current input with the previous responses
    for message in reversed(conversation_history):
        if message["role"] == "assistant":
            similarity = fuzz.ratio(user_input.lower(), message["content"].lower())
            if similarity > 70:
                print(f"Chatbot: It seems like you've asked a similar question before. Here's a related response: {message['content']}")
                break
