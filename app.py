from fastapi import FastAPI, Form, HTTPException, Request
from fetch_labels import router as ProcessForm
from chat import router as ChatResponse

app = FastAPI()

app.include_router(ProcessForm, tags=["Labels"], prefix="/Openai/FetchLabel")
app.include_router(ChatResponse, tags=["ChatOpenai"], prefix="/Openai/chat")
