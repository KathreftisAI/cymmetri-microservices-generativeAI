import os
import openai
import gradio as gr

openai.api_type = "azure"
openai.api_base = "https://cymetriopen.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = "ebe64320148849aead404cc3aec9cc49"

prompt = [{"role": "system", "content": "You are an AI assistant that helps people find information."}]

def openai_create(prompt):
    response = openai.ChatCompletion.create(
        engine="tesrt",
        messages=prompt,
        temperature=0.7,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return response.choices[0].content

def conversation_history(input, history):
    history = history or []
    history.append({"role": "user", "content": input})
    output = openai_create(history)
    history.append({"role": "assistant", "content": output})
    return history, history

blocks = gr.Blocks()

with blocks:
    chatbot = gr.Chatbot()
    message = gr.Textbox(placeholder="Type here")
    state = gr.State()
    submit = gr.Button("Submit")
    input_vals = [message, state]
    submit.click(conversation_history, inputs=input_vals, outputs=[chatbot, state])

blocks.launch(debug=True)
