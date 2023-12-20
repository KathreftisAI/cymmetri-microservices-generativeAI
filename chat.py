import os
from fastapi import FastAPI, Form, HTTPException, Request
import openai
import json
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse 
from pydantic import BaseModel
import uvicorn
from func import extract_labels_from_record, get_response_text, format_mapped_elements, chat_with_bot 
from motor.motor_asyncio import AsyncIOMotorClient


openai.api_type = "azure"
openai.api_base = "https://cymetriopen.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = "ebe64320148849aead404cc3aec9cc49"
 
#app = FastAPI()
router = APIRouter()
templates = Jinja2Templates(directory="templates")

        

@router.post("/chat")
async def chat_endpoint(request: Request, syntax: str = Form(...), db_name2: str = Form(...),
    collection_name2: str = Form(...), labels1: str = Form(...)):
    l1 = labels1.split('|') if labels1 else []
    seed_value = 10

    mongo_connection_string = (
            "mongodb://unoadmin:devDb123@10.0.1.6:27019,10.0.1.6:27020,10.0.1.6:27021/"
            "?authSource=admin&replicaSet=sso-rs&retryWrites=true&w=majority"
        )
    mongo_client = AsyncIOMotorClient(mongo_connection_string)
    mongo_db2 = mongo_client[db_name2]
    mongo_collection2 = mongo_db2[collection_name2]
    mongo_data2 = await mongo_collection2.find().to_list(length=None)


    if len(mongo_data2) > 0:
        sample_record2 = mongo_data2[0]
        labels2 = extract_labels_from_record(sample_record2)
    else:
        labels2 = []

    l2 = labels2
  
    bot_reply = chat_with_bot(l1, l2, syntax,seed=seed_value)

    # Calculate matched and unmatched elements for L1 and L2
    l1_matched = [label for label in l1 if label in bot_reply]
    l2_matched = [label for label in l2 if label in bot_reply]

    l1_unmatched = list(set(l1) - set(l1_matched))
    l2_unmatched = list(set(l2) - set(l2_matched))

    # Now you have l1_matched, l2_matched, l1_unmatched, and l2_unmatched available for further use
    return {
        "bot_reply": bot_reply,
        "l1_matched": l1_matched,
        "l2_matched": l2_matched,
        "l1_unmatched": l1_unmatched,
        "l2_unmatched": l2_unmatched
    }
    #return {"bot_reply":bot_reply}
