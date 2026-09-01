import os
import sys
import json
import asyncio
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Base directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

ENV_PATH = os.path.join(BASE_DIR, ".env")
if os.path.exists(ENV_PATH):
    load_dotenv(dotenv_path=ENV_PATH, override=True)

from ghl_client import GHLSubAccountClient
from agent_engine import GHLAgentExecutionEngine, MODELS_CATALOG, format_friendly_error_banner
from usage_tracker import usage_tracker
from key_pool_manager import openrouter_key_pool, gemini_key_pool

def get_server_keys() -> Dict[str, str]:
    """Load API keys for Gemini, Groq, and active OpenRouter key from the dynamic pool."""
    active_or_key = openrouter_key_pool.get_active_key() or os.getenv("OPENROUTER_API_KEY", "").strip()
    active_gemini_key = gemini_key_pool.get_active_key() or os.getenv("GEMINI_API_KEY", "").strip()
    return {
        "gemini": active_gemini_key,
        "groq": os.getenv("GROQ_API_KEY", "").strip(),
        "openrouter": active_or_key
    }

app = FastAPI(
    title="Conversation AI Copilot for GoHighLevel",
    description="Multi-Model Autonomous Action Execution Agent for GoHighLevel with Live Usage Tracking",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class AttachmentItem(BaseModel):
    name: str
    type: str = "file"  # 'image' or 'file'
    mime_type: Optional[str] = ""
    data: str = ""  # Base64 data URL or raw text
    size: Optional[int] = 0

class AgentChatRequest(BaseModel):
    prompt: str
    location_id: Optional[str] = ""
    access_token: Optional[str] = ""
    selected_model: Optional[str] = "groq/compound-mini"
    history: Optional[List[Dict[str, Any]]] = []
    attachments: Optional[List[AttachmentItem]] = []

class VerifyTokenRequest(BaseModel):
    location_id: str
    access_token: str

@app.get("/health")
async def health_check():
    keys = get_server_keys()
    return {
        "status": "online",
        "service": "Conversation AI Copilot",
        "port": 7861,
        "providers": {
            "groq": bool(keys["groq"] and keys["groq"] != "YOUR_GROQ_API_KEY_HERE")
        }
    }

@app.get("/api/models")
async def get_models_catalog():
    """Returns the list of all available Groq AI models with live usage statistics."""
    keys = get_server_keys()
    enriched_models = []
    
    for m in MODELS_CATALOG:
        m_copy = dict(m)
        stats = usage_tracker.get_model_stats(m["id"])
        m_copy["usage"] = stats
        enriched_models.append(m_copy)

    return {
        "models": enriched_models,
        "active_providers": {
            "groq": bool(keys["groq"])
        },
        "default_model": "groq/compound-mini"
    }

@app.get("/api/usage-stats")
async def get_all_usage_stats():
    """Returns full usage monitoring summary for all models."""
    res = {}
    for m in MODELS_CATALOG:
        res[m["id"]] = usage_tracker.get_model_stats(m["id"])
    return {"success": True, "stats": res}

@app.get("/api/openrouter/pool-status")
async def get_openrouter_pool_status():
    """Returns real-time credit status and active rotation state for OpenRouter key pool."""
    openrouter_key_pool.poll_all_keys()
    return {
        "success": True,
        "active_key": openrouter_key_pool.get_active_key(),
        "pool": openrouter_key_pool.get_pool_status()
    }

@app.post("/api/ghl/verify-token")
async def verify_ghl_token(req: VerifyTokenRequest):
    client = GHLSubAccountClient(location_id=req.location_id, access_token=req.access_token)
    res = client.verify_connection()
    return res

@app.post("/api/ghl/contacts")
async def get_ghl_contacts(req: VerifyTokenRequest):
    client = GHLSubAccountClient(location_id=req.location_id, access_token=req.access_token)
    res = client.search_contacts(query="")
    return res

@app.post("/api/ghl/create-contact")
async def create_ghl_contact_manual(req: Dict[str, Any]):
    loc_id = req.get("location_id", "")
    token = req.get("access_token", "")
    first_name = req.get("first_name", "").strip()
    last_name = req.get("last_name", "").strip()
    email = req.get("email", "").strip()
    phone = req.get("phone", "").strip()
    tag = req.get("tag", "").strip()

    if not first_name:
        raise HTTPException(status_code=400, detail="First Name is required.")

    client = GHLSubAccountClient(location_id=loc_id, access_token=token)
    res = client.create_contact(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        tags=[tag] if tag else None
    )
    return res

@app.post("/api/ghl/pipelines")
async def get_ghl_pipelines(req: VerifyTokenRequest):
    client = GHLSubAccountClient(location_id=req.location_id, access_token=req.access_token)
    res = client.get_pipelines()
    return res

@app.post("/api/ghl/tags")
async def get_ghl_tags(req: VerifyTokenRequest):
    client = GHLSubAccountClient(location_id=req.location_id, access_token=req.access_token)
    res = client.get_tags()
    return res

@app.post("/api/ghl/custom-fields")
async def get_ghl_custom_fields(req: VerifyTokenRequest):
    client = GHLSubAccountClient(location_id=req.location_id, access_token=req.access_token)
    res = client.get_custom_fields()
    return res

@app.post("/api/ghl/setup-gym")
async def setup_gym_architecture_endpoint(req: VerifyTokenRequest):
    client = GHLSubAccountClient(location_id=req.location_id, access_token=req.access_token)
    res = client.setup_gym_subaccount()
    return res

@app.post("/api/chat-agent")
async def agent_chat_endpoint(req: AgentChatRequest):
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt string cannot be empty.")

    keys = get_server_keys()
    engine = GHLAgentExecutionEngine(
        gemini_key=keys["gemini"],
        groq_key=keys["groq"],
        openrouter_key=keys["openrouter"]
    )

    selected_model = req.selected_model or "gemini-3.6-flash"

    # Track usage stats
    estimated_tokens = max(50, len(prompt) // 4 + 200)
    usage_tracker.record_usage(selected_model, tokens_est=estimated_tokens)

    raw_attachments = [a.model_dump() for a in req.attachments] if req.attachments else []

    async def sse_generator():
        try:
            generator = engine.execute_agent_prompt(
                prompt=prompt,
                location_id=req.location_id or "",
                access_token=req.access_token or "",
                model_name=selected_model,
                history=req.history or [],
                attachments=raw_attachments
            )
            for item in generator:
                yield f"data: {json.dumps(item)}\n\n"
                await asyncio.sleep(0)
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"Chat streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'chunk', 'text': format_friendly_error_banner(str(e))})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

# Mount Static Files
STATIC_DIR = os.path.join(BASE_DIR, "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Conversation AI Copilot API is running."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7861))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"🚀 Launching Conversation AI Copilot on http://{host}:{port} ...")
    uvicorn.run("app:app", host=host, port=port, reload=False)

    