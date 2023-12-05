import os
import openai
from fuzzywuzzy import fuzz

openai.api_type = "azure"
openai.api_base = "https://cymetriopen.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = "ebe64320148849aead404cc3aec9cc49"

# Maintain conversation history
conversation_history = []

continue_conversation = True

def get_response_text(response):
    try:
        # Attempt to get the text content from the response
        text_content = response['choices'][0]['message']['content']
        return text_content
    except (KeyError, IndexError):
        return None

def compare_lists_fuzzy(l1, l2):
    matching_elements = []
    for item1 in l1:
        for item2 in l2:
            # Using fuzzy ratio to compare elements
            similarity_ratio = fuzz.ratio(item1, item2)
            # You can adjust the threshold based on your requirements
            if similarity_ratio > 80:  # Adjust the threshold as needed
                matching_elements.append((item1, item2, similarity_ratio))
    return matching_elements

def chat_with_bot(user_input):
    # Initialize the conversation with system and user messages
    conversation_history.append({"role": "user", "content": user_input})

    if "l1" in user_input.lower() and "l2" in user_input.lower():
        # Extract lists from user input
        l1 = input("Enter elements for list l1 (comma-separated): ").split(",")
        l2 = input("Enter elements for list l2 (comma-separated): ").split()
        
        # Compare lists based on fuzzy logic
        matching_elements = compare_lists_fuzzy(l1, l2)
        response = f"The matching elements based on fuzzy logic are: {matching_elements}"
        print("Bot:", response)
    else:
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
