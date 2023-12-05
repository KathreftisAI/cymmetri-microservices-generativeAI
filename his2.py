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
    print("Bot:", response)
 
    conversation_history.append({"role": "assistant", "content": response})
 
    return response
 
def regenerate_response(previous_question):
    completion = openai.ChatCompletion.create(
        engine="tesrt",
        messages=[
            {"role": "system", "content": "You are an AI assistant that helps people find information."},
            {"role": "user", "content": previous_question}
        ],
        temperature=0.4,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
 
    response = get_response_text(completion)
    return response
 
print("Chatbot: Hello! How can I assist you today?")
 
while True:
    print("You :")
    user_input_lines = []
 
    while True:
        line = input()
        if line.lower() == 'exit':
            break
        elif not line.strip() and user_input_lines and not user_input_lines[-1].strip():
            break
        user_input_lines.append(line)
 
    user_input = '\n'.join(user_input_lines)
 
    if user_input.lower() == 'exit':
        print("Chatbot: Goodbye!")
        break
 
    bot_reply = chat_with_bot(user_input)
 
    if user_input.lower() == 'regenerate':
        previous_question = None
        for message in reversed(conversation_history):
            if message["role"] == "assistant":
                previous_question = message['content']
                break
 
        if previous_question:
            regenerated_response = regenerate_response(previous_question)
            print("Chatbot: Here's a different response linked to your previous question:")
            print("Bot:", regenerated_response)
            conversation_history.append({"role": "assistant", "content": regenerated_response})
        else:
            print("Chatbot: Sorry, there's no previous question to generate a response.")
            continue
 
    for message in reversed(conversation_history):
        if message["role"] == "assistant":
            similarity = fuzz.ratio(user_input.lower(), message["content"].lower())
            if similarity > 70:
                print(f"Chatbot: It seems like you've asked a similar question before. Here's a related response: {message['content']}")
                break