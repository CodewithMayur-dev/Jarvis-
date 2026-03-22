#!/usr/bin/env python3
"""
JARVIS REST API — Nepal INC
Powers iOS, Android, Web clients
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

sys.path.insert(0, '/root/jarvis')
from brain import Brain
from memory import Memory
from tools import Tools
from journal import write_mayur_entry, read_recent

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("JARVIS-API")

memory = Memory()
tools  = Tools()
brain  = Brain(memory=memory, tools=tools)

API_KEYS = {
    "nepal-inc-mayur-2026": "mayur",
    "nepal-inc-ios-2026":   "ios_user",
    "nepal-inc-web-2026":   "web_user",
}

def verify_key(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return API_KEYS[x_api_key]

app = FastAPI(
    title="JARVIS API",
    description="Nepal INC — JARVIS AI Assistant API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[str] = "api_user"

class JournalRequest(BaseModel):
    entry: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str

@app.get("/")
async def root():
    return {
        "name": "JARVIS API",
        "company": "Nepal INC",
        "version": "1.0.0",
        "status": "online",
        "built_by": "Mayur Anand Shah"
    }

@app.get("/health")
async def health():
    return {"status": "online", "timestamp": datetime.now().isoformat()}

@app.get("/status")
async def status(x_api_key: str = Header(None)):
    user = verify_key(x_api_key)
    return {
        "status": "online",
        "user": user,
        "providers": {
            "gemini":   len(brain.router._keys["gemini"]),
            "groq":     len(brain.router._keys["groq"]),
            "deepseek": len(brain.router._keys["deepseek"])
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat")
async def chat(req: ChatRequest, x_api_key: str = Header(None)):
    user = verify_key(x_api_key)
    log.info(f"Chat from {user}: {req.message[:50]}")
    try:
        response = await brain.think(req.message, req.chat_id)
        return {"response": response, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/journal")
async def journal(req: JournalRequest, x_api_key: str = Header(None)):
    verify_key(x_api_key)
    try:
        jarvis_entry = write_mayur_entry(
            req.entry,
            lambda p: brain.router.call(p, [])
        )
        return {
            "success": True,
            "mayur_entry": req.entry,
            "jarvis_entry": jarvis_entry,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/journal/read")
async def read_journal(x_api_key: str = Header(None)):
    verify_key(x_api_key)
    return {"journal": read_recent(), "timestamp": datetime.now().isoformat()}
