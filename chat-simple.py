import os
import openai

openai.api_type = "azure"
openai.api_base = "https://cymetriopen.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = "ebe64320148849aead404cc3aec9cc49"

#Maintain conversation history
conversation_history = []

continue_conversation = True


def get_response_text(response):
    try:
        # Attempt to get the text content from the response
        text_content = response['choices'][0]['message']['content']
        return text_content
    except (KeyError, IndexError):
        return None

def chat_with_bot(user_input):
    # Initialize the conversation with system and user messages
    conversation_history.append({"role": "user","content": user_input})

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

    # Print the assistant's response
    response = get_response_text(completion)

    conversation_history.append({"role": "assistant", "content": response})
    print("Bot:", response)
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
    # compare this two fields based on fuzzy logic and give me matching fields from this two list