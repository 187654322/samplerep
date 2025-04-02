from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sqlalchemy import ForeignKey, String, create_engine, Column, Integer, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime
import redis
from user_chat_service import get_ai_response
from db_connectivity_service import processAnalitics
from handle_knowledge_base import handle_knowledge_base
from table_structure_service import update_table_structure

# FastAPI App Setup
app = FastAPI(title="Vox AI Assistant", description="AI-powered database query and conversation assistant")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# Initialize the embedding model
embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

# Set API Key for OpenRouter (Mistral 24B)
MISTRAL_API_KEY = [
    os.getenv("OPENROUTER_API_KEY", "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"),
    os.getenv("SECONDARY_API_KEY", "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"),
    os.getenv("THIRD_API_KEY", "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"),
]

MISTRAL_API_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.put("/api/update_kb/{xt_vox_id}")
async def process_knowledge_base(xt_vox_id: str):
    try:
        handle_knowledge_base(embedding_model, xt_vox_id)
        return {"content": "Knowledge Base Successfully updated"}, 200
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Start a New Conversation and Reset Local History
@app.post("/new_conversation")
async def new_conversation():
    return {"message": "New conversation started."}

# Pydantic Models for Request Validation
class ChatRequest(BaseModel):
    xt_vox_id: str
    message: str

# Chat API Endpoint
@app.post("/api/chat")
async def chat(request: ChatRequest):    
    user_message = request.message
    xt_vox_id = request.xt_vox_id
    try:
        ai_response = get_ai_response(user_message, embedding_model, xt_vox_id, MISTRAL_API_KEY, MISTRAL_API_URL)
        return {"response": ai_response}, 200
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class UserNotFound(Exception):
    def __init__(self, xt_vox_id, msg="User Not Found"):
        self.xt_vox_id = xt_vox_id
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self):
        return f'{self.xt_vox_id} -> {self.msg}'
    

class NoDataBaseException(Exception):
    def __init__(self, xt_vox_id, msg=f"No databse found for this user:"):
        self.xt_vox_id = xt_vox_id
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self):
        return f'{self.xt_vox_id} -> {self.msg}'


# Exception Handlers
@app.exception_handler(UserNotFound)
async def user_not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": f"{exc.xt_vox_id} {exc.msg}"}
    )

@app.exception_handler(NoDataBaseException)
async def no_database_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": f"{exc.msg} {exc.xt_vox_id}"}
    )

class AnalyticsRequest(BaseModel):
    voxId: str
    message: str
    # dbStructure: str = None

@app.post('/api/db-query')
async def processDatabaseRequest(request : AnalyticsRequest):
    try:
        xt_vox_id = request.voxId
        user_message = request.message
        Db_structure = None

        if Db_structure is None:
            Db_structure = redis_client.get(xt_vox_id)
        else:
            redis_client.set(xt_vox_id, Db_structure)
            
        if Db_structure is None:
            return {"error": "Invalid Payload dbStructure required"}, 400

        imageString, queryResult = processAnalitics(xt_vox_id, user_message)
        return {"responseMessage": imageString, "resultData": queryResult}, 200
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.put('/api/update-table-structure/{xt_vox_id}')
async def updateTableStructure(xt_vox_id: str):
    try:
        update_table_structure(redis_client, xt_vox_id)
        return {"content": "Successfully updated"}, 200
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)