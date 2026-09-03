import os
import re
import json
import base64
import logging
import requests
from typing import Dict, Any, List, Generator, Optional, Tuple
from google import genai
from google.genai import types

from ghl_client import GHLSubAccountClient
from portfolio_knowledge_base import agency_portfolio_kb

logger = logging.getLogger(__name__)


def process_attachments_for_prompt(prompt: str, attachments: Optional[List[Dict[str, Any]]]) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Processes incoming attachments (images, PDFs, documents, CSVs, JSON, code).
    Returns (augmented_prompt, image_items).
    """
    if not attachments:
        return prompt, []

    doc_sections = []
    image_items = []

    for att in attachments:
        name = att.get("name", "attachment")
        att_type = att.get("type", "file")
        mime = att.get("mime_type", "")
        data = att.get("data", "")

        if att_type == "image" or mime.startswith("image/"):
            image_items.append(att)
            doc_sections.append(f"🖼️ **ATTACHED IMAGE:** {name} ({mime or 'image'})")
        else:
            doc_content = ""
            if data.startswith("data:"):
                try:
                    header, b64 = data.split(",", 1)
                    decoded = base64.b64decode(b64).decode("utf-8", errors="replace")
                    doc_content = decoded
                except Exception:
                    doc_content = f"[Binary Document: {name}]"
            else:
                doc_content = data

            doc_sections.append(f"📄 **ATTACHED DOCUMENT: {name}**\n```\n{doc_content}\n```\n")

    augmented_prompt = prompt
    if doc_sections:
        docs_block = "\n\n".join(doc_sections)
        augmented_prompt = f"--- USER ATTACHED FILES ---\n{docs_block}\n--- USER QUERY ---\n{prompt}"

    return augmented_prompt, image_items


# =====================================================================
# INTELLIGENT PROMPT ANALYSIS & ADAPTIVE CONFIGURATION ENGINE
# =====================================================================

# Compiled regex patterns for prompt intent classification
_FULL_BUILD_PATTERNS = re.compile(
    r'^(build|create|make|design|generate|deploy|setup|implement|develop|architect)\s+'
    r'(me\s+)?(a\s+)?(complete|full|production|enterprise|entire|comprehensive|'
    r'landing\s*page|funnel|crm|pipeline\s*architecture|sub-?account\s*architecture|'
    r'architecture|gohighlevel\s+architecture)',
    re.IGNORECASE
)
_PROPOSAL_OR_QA_PATTERNS = re.compile(
    r'(we are looking for|looking for|job\s+post|apply|application|hiring|interview|'
    r'who are you|when you respond|scope of work|done-with-you|done with you|'
    r'kia theek|kia ghlat|kya theek|kya ghlat|theek ha|ghlat ha|feedback|audit)',
    re.IGNORECASE
)
_ITERATION_PATTERNS = re.compile(
    r'^(change|modify|update|edit|tweak|adjust|fix|improve|darker|lighter|blue|red|green|'
    r'add\s+a|remove\s+the|make\s+it|replace|swap|rename|move|instead)\b',
    re.IGNORECASE
)
_FULL_BUILD_KEYWORDS = {
    'configuration:', 'target industry:', '1a', '2a', '3a', '4a', '5a',
    'option 1', 'option a', 'all 14 sections', 'full blueprint',
    'brand customization:', 'connected automations:', 'custom wizard specifications:',
    'html/css', 'html and css', 'provide the html', 'checkout html', 'funnel architecture',
    'deep improvement', 'code review', 'implementation review', 'production ready code',
    'production-ready', 'review the uploaded', 'architectural review', 'vsl funnel'
}

_DIRECT_ASSET_PATTERNS = re.compile(
    r'^(create|build|add|make|set\s*up|configure)\s+(a\s+)?(pipeline|tag|contact|custom\s+field|opportunity|stage)\b',
    re.IGNORECASE
)


def classify_prompt_intent(prompt: str) -> str:
    """
    Classifies user prompt into one of three intent categories:
    - 'full_build': Explicit request to build full landing page & CRM architecture or write code
    - 'iteration': Modify or refine a previous response
    - 'quick_answer': Q&A, job proposals, consultation, troubleshooting, or direct asset creation
    """
    lower = prompt.lower().strip()

    # Direct single asset creation commands (pipeline, tag, contact, custom field) -> quick_answer / focused response
    if _DIRECT_ASSET_PATTERNS.search(lower) and not any(kw in lower for kw in ['all 14 sections', 'full blueprint', 'complete funnel', 'landing page and crm']):
        return 'quick_answer'

    # If prompt mentions changing/modifying design, color, styling, or has an attached document being updated
    if any(phrase in lower for phrase in [
        'need changes in', 'changes in its', 'change the color', 'change design', 'color scheme',
        'update the design', 'modify the code', 'tweak the design', 'make changes', 'change in it',
        'liked it but', 'good but i need', 'good, but i need', 'user attached files'
    ]) and not any(kw in lower for kw in ['configuration:', 'target industry:', 'all 14 sections']):
        return 'iteration'

    # Check for direct full build commands
    if _FULL_BUILD_PATTERNS.search(lower):
        return 'full_build'

    # Explicit full build markers from Wizard or structured commands
    if any(kw in lower for kw in _FULL_BUILD_KEYWORDS):
        return 'full_build'

    # Check for iteration / modification intent
    if _ITERATION_PATTERNS.search(lower):
        return 'iteration'

    # If prompt is explicitly a proposal or simple feedback, classify as quick_answer
    if _PROPOSAL_OR_QA_PATTERNS.search(lower):
        return 'quick_answer'

    # Default: quick answer for simple questions
    return 'quick_answer'



def format_friendly_error_banner(reason: str = "") -> str:
    """
    Returns a clean, polished, user-friendly error card when any AI provider
    or server fails to generate a response.
    """
    return (
        "> ⚠️ **System Notice: Unable to Generate Response**\n"
        ">\n"
        "> The AI engine is temporarily unable to generate a response at this moment due to high upstream traffic or model quota limits.\n"
        ">\n"
        "> 💡 **What you can do:**\n"
        "> • **Try again in a few moments** — temporary network/provider limits usually clear within seconds.\n"
        "> • **Switch AI Model** — Select **✨ Gemini 3.6 Flash** or **Groq Cloud** from the model dropdown below.\n"
        "> • **Shorten your query** — If uploading large documents or complex requests, try breaking them into focused steps."
    )


# Per-model actual output token ceilings (verified from provider docs)
MODEL_OUTPUT_CAPS = {
    'gemini-3.6-flash': 8192,
    'gemini-3.7-flash': 8192,
    'groq/compound-mini': 4096,
    'qwen/qwen3.8-27b': 4096,
    'x-ai/grok-4.6': 8192,
    'meta-llama/llama-3.3-70b-instruct': 4096,
}

def get_token_budget(provider: str, intent: str, model_name: str = '') -> int:
    """
    Returns the optimal max_tokens for a given provider × intent combination,
    capped by the model's actual output ceiling.
    """
    budgets = {
        'groq': {
            'full_build': 8192,
            'iteration': 6000,
            'quick_answer': 4000,
        },
        'gemini': {
            'full_build': 8192,
            'iteration': 6000,
            'quick_answer': 4000,
        },
        'openrouter': {
            'full_build': 4000,
            'iteration': 2500,
            'quick_answer': 1500,
        }
    }
    requested = budgets.get(provider, budgets['groq']).get(intent, 4000)
    cap = MODEL_OUTPUT_CAPS.get(model_name, 8192)
    return min(requested, cap)


def get_temperature(intent: str, is_tool_mode: bool = False) -> float:
    """
    Returns adaptive temperature based on task type.

    Tool-calling always uses 0.1 for deterministic function invocation.
    Creative tasks (HTML/CSS/copy) use higher temperature for variety.
    """
    if is_tool_mode:
        return 0.1

    temps = {
        'full_build': 0.7,
        'iteration': 0.4,
        'quick_answer': 0.2,
    }
    return temps.get(intent, 0.2)


def get_thinking_budget(intent: str) -> int:
    """
    Returns thinking budget for models.
    Returns 0 for instantaneous streaming response with zero initial pause.
    """
    return 0


def compress_history(
    history: List[Dict[str, str]],
    provider: str,
    max_messages: int = 0,
    intent: str = "quick_answer"
) -> List[Dict[str, str]]:
    """
    Intelligently compresses conversation history while strictly preserving alternating turn structure.
    Prevents token waste, avoids context pollution, and ensures previous Q&A turns are not re-answered.
    """
    if not history:
        return []

    # For full_build: keep ONLY the last 2 user messages (brand context) but drop large assistant responses
    if intent == "full_build":
        user_msgs = [m for m in history if m.get('role') == 'user']
        if not user_msgs:
            return []
        kept = user_msgs[-2:]  # Last 2 user messages with requirements/brand info
        return [{'role': 'user', 'content': m.get('content', '')[:600]} for m in kept]

    if max_messages <= 0:
        max_messages = 6 if provider == 'gemini' else 4

    trimmed = list(history[-max_messages:])
    # For iteration: preserve full previous code/document context (up to 35,000 chars) so model knows the exact code to edit!
    if intent == "iteration":
        max_assistant_chars = 35000
    else:
        max_assistant_chars = 1000 if provider == 'groq' else 2500

    compressed = []
    for msg in trimmed:
        role = msg.get('role', 'user')
        if role in ['model', 'assistant']:
            role = 'assistant'
        content = msg.get('content', '').strip()
        if not content:
            continue
            
        if role == 'assistant' and len(content) > max_assistant_chars:
            compressed.append({
                'role': 'assistant',
                'content': content[:max_assistant_chars] + '\n\n[... previous response summarized ...]'
            })
        else:
            compressed.append({'role': role, 'content': content})

    # Ensure alternating turn discipline (never send consecutive user or assistant messages)
    sanitized = []
    for msg in compressed:
        if sanitized and sanitized[-1]['role'] == msg['role']:
            sanitized[-1]['content'] += "\n" + msg['content']
        else:
            sanitized.append(msg)

    # If history ends with 'user', remove it because the new prompt will be appended as the active 'user' turn
    if sanitized and sanitized[-1]['role'] == 'user':
        sanitized.pop()

    return sanitized


def detect_truncation(text: str) -> bool:
    """
    Detects if a response was genuinely truncated mid-generation.
    Only triggers on definitive structural indicators, NOT on natural conclusions.
    """
    if not text or len(text) < 150:
        return False

    # Check if an HTML application was started but </html> was not closed
    if "<!DOCTYPE html" in text or "<html" in text:
        if "</html>" not in text:
            return True

    # Check for unclosed markdown code fences
    fence_count = text.count('```')
    if fence_count % 2 != 0:
        return True

    # Check if output ended abruptly mid-token, mid-sentence, or mid-tag
    clean_end = text.rstrip()
    if clean_end and clean_end[-1] in ('<', '=', '{', '[', '•', '-'):
        return True

    # In full_build: if workflows were started (e.g. Workflow 1), check that later workflows exist
    lower = text.lower()
    if "task directive: complete production" in lower or "step 1: opt-in" in lower:
        if "workflow 1" in lower and not any(w in lower for w in ["workflow 4", "workflow 5", "summary", "post-funnel"]):
            return True

    return False

# AI Models Catalog categorized by Provider (Top 4 Clean High-Performance Models)
MODELS_CATALOG = [
    # Google Gemini Models (Active Key Pool)
    {
        "id": "gemini-3.6-flash",
        "name": "Gemini 3.6 Flash (Recommended)",
        "provider": "gemini",
        "category": "Google Gemini",
        "badge": "✨ 1M TPM • Tools",
        "supports_tools": True,
        "description": "State-of-the-art multimodal Gemini model with native GHL function calling and ultra high speed."
    },
    {
        "id": "gemini-3.7-flash",
        "name": "Gemini 3.7 Flash",
        "provider": "gemini",
        "category": "Google Gemini",
        "badge": "🧠 Advanced Reasoning",
        "supports_tools": True,
        "description": "Hybrid reasoning model for high precision CRM workflows and complex multi-step automations."
    },

    # Groq Cloud Ultra-Fast LPUs
    {
        "id": "groq/compound-mini",
        "name": "Groq Compound Mini",
        "provider": "groq",
        "category": "Groq Ultra-Fast",
        "badge": "⚡ 70k TPM Ultra",
        "supports_tools": True,
        "description": "High-throughput Groq Compound model with ~70k TPM capacity for massive multi-step funnels."
    },
    {
        "id": "qwen/qwen3.8-27b",
        "name": "Groq Qwen 3.8 27B",
        "provider": "groq",
        "category": "Groq Ultra-Fast",
        "badge": "⚡ Low Latency LPU",
        "supports_tools": True,
        "description": "Lightning-fast open-weights execution on Groq LPU with full GHL function calling."
    },

    # Puter.js Free In-Browser AI (Commented out to prioritize direct ultra-fast API speeds)
    # {
    #     "id": "x-ai/grok-4.6",
    #     "name": "xAI Grok 3 Mini (Puter.js Free)",
    #     "provider": "puter",
    #     "category": "Puter.js Free AI",
    #     "badge": "⚡ Free • Fast xAI",
    #     "supports_tools": False,
    #     "description": "Fast xAI Grok 3 Mini via Puter.js — instant responses, no thinking delay. Runs client-side, zero API key, completely free."
    # },

    # OpenRouter Multi-Key Pool Gateway
    {
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "Llama 3.3 70B (OpenRouter Pool)",
        "provider": "openrouter",
        "category": "OpenRouter Gateway",
        "badge": "🌐 6-Key Pool • Tools",
        "supports_tools": True,
        "description": "High-capacity Llama 3.3 70B Instruct with auto-failover across 6 OpenRouter pool keys."
    }
]

# Declare Function Tools for Gemini AI Agent
GHL_TOOLS_DECLARATIONS = [
    {
        "name": "create_contact",
        "description": "Create a new contact in the GoHighLevel Sub-Account.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "first_name": {"type": "STRING", "description": "First name of contact"},
                "last_name": {"type": "STRING", "description": "Last name of contact"},
                "email": {"type": "STRING", "description": "Email address"},
                "phone": {"type": "STRING", "description": "Phone number"},
                "tags": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Tags list (e.g. ['VIP', 'Lead'])"}
            },
            "required": ["first_name"]
        }
    },
    {
        "name": "search_contacts",
        "description": "Search contacts in the sub-account by name, email, or phone.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "Search keyword or email/phone"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_pipeline",
        "description": "Create a new Sales / Opportunity Pipeline with stages.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING", "description": "Name of the pipeline (e.g. Solar Sales)"},
                "stages": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Stage names list (e.g. ['New Lead', 'Booked', 'Won'])"}
            },
            "required": ["name", "stages"]
        }
    },
    {
        "name": "get_pipelines",
        "description": "Fetch all pipelines and stages in the sub-account.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "create_opportunity",
        "description": "Create an Opportunity deal card in a pipeline stage.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "pipeline_id": {"type": "STRING", "description": "ID of target pipeline"},
                "stage_id": {"type": "STRING", "description": "ID of target stage"},
                "title": {"type": "STRING", "description": "Opportunity / Deal title"},
                "status": {"type": "STRING", "description": "Status (open, won, lost, abandoned)"},
                "monetary_value": {"type": "NUMBER", "description": "Monetary value of deal"}
            },
            "required": ["pipeline_id", "stage_id", "title"]
        }
    },
    {
        "name": "create_tag",
        "description": "Create a new Tag in the sub-account.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "tag_name": {"type": "STRING", "description": "Name of the tag to create"}
            },
            "required": ["tag_name"]
        }
    },
    {
        "name": "create_custom_field",
        "description": "Create a Custom Field (TEXT, NUMBER, DATE, SINGLE_OPTIONS, etc.) in the sub-account.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING", "description": "Name of custom field"},
                "data_type": {"type": "STRING", "description": "Data type: TEXT, NUMBER, DATE, SINGLE_OPTIONS"},
                "options": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "List of options for SINGLE_OPTIONS or dropdown fields"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "send_conversation_message",
        "description": "Send an SMS or Email message to a contact in GHL.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "contact_id": {"type": "STRING", "description": "ID of recipient contact"},
                "message": {"type": "STRING", "description": "Message text"},
                "type_": {"type": "STRING", "description": "SMS or Email"}
            },
            "required": ["contact_id", "message"]
        }
    },
    {
        "name": "create_contact_task",
        "description": "Create a Task for a contact in GHL Sub-Account",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "contact_id": {"type": "STRING", "description": "GHL Contact ID"},
                "title": {"type": "STRING", "description": "Task title"},
                "due_date": {"type": "STRING", "description": "Optional due date ISO string"}
            },
            "required": ["contact_id", "title"]
        }
    },
    {
        "name": "create_contact_note",
        "description": "Add an internal note to a contact in GHL Sub-Account",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "contact_id": {"type": "STRING", "description": "GHL Contact ID"},
                "body": {"type": "STRING", "description": "Note body text"}
            },
            "required": ["contact_id", "body"]
        }
    },
    {
        "name": "setup_gym_subaccount",
        "description": "Deploy complete Gym / Fitness Center Sub-Account Architecture (Custom Fields, Tags, Pipelines)",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    }
]

def get_openai_tools_schema() -> List[Dict[str, Any]]:
    """Converts Gemini tool declarations to OpenAI/OpenRouter/Groq format."""
    type_map = {
        "OBJECT": "object",
        "STRING": "string",
        "ARRAY": "array",
        "NUMBER": "number",
        "INTEGER": "integer",
        "BOOLEAN": "boolean"
    }
    openai_tools = []
    for decl in GHL_TOOLS_DECLARATIONS:
        props = {}
        for p_name, p_info in decl["parameters"].get("properties", {}).items():
            p_type = type_map.get(p_info.get("type", "STRING"), "string")
            p_dict = {"type": p_type, "description": p_info.get("description", "")}
            if p_type == "array" and "items" in p_info:
                p_dict["items"] = {"type": type_map.get(p_info["items"].get("type", "STRING"), "string")}
            props[p_name] = p_dict
        
        openai_tools.append({
            "type": "function",
            "function": {
                "name": decl["name"],
                "description": decl["description"],
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": decl["parameters"].get("required", [])
                }
            }
        })
    return openai_tools


def detect_provider(model_name: str) -> str:
    """Detects provider from model slug."""
    model_name = (model_name or "").strip().lower()
    for item in MODELS_CATALOG:
        if item["id"].lower() == model_name:
            return item["provider"]
    if "openrouter" in model_name or "llama" in model_name:
        return "openrouter"
    if "puter" in model_name or "grok" in model_name:
        return "puter"
    if "rapidapi" in model_name:
        return "rapidapi"
    if model_name.startswith("gemini-"):
        return "gemini"
    return "groq"


def stream_text_tokens(text: str) -> Generator[Dict[str, Any], None, None]:
    """Splits full text into small tokenized chunks for smooth SSE streaming."""
    if not text:
        return
    import re
    tokens = re.findall(r'\S+\s*|\s+', text)
    buffer = ""
    for tok in tokens:
        buffer += tok
        if len(buffer) >= 14 or "\n" in tok:
            yield {"type": "chunk", "text": buffer}
            buffer = ""
    if buffer:
        yield {"type": "chunk", "text": buffer}


class GHLAgentExecutionEngine:
    """
    High-Performance AI Action Execution Engine for GoHighLevel supporting Google Gemini, Groq Cloud, and RapidAPI.
    """
    def __init__(self, gemini_key: str = "", groq_key: str = "", openrouter_key: str = "", rapidapi_key: str = "", rapidapi_host: str = ""):
        from key_pool_manager import gemini_key_pool, openrouter_key_pool
        self.gemini_key = gemini_key.strip() or gemini_key_pool.get_active_key() or os.getenv("GEMINI_API_KEY", "").strip()
        self.groq_key = groq_key.strip() or os.getenv("GROQ_API_KEY", "").strip()
        self.openrouter_key = openrouter_key.strip() or openrouter_key_pool.get_active_key() or os.getenv("OPENROUTER_API_KEY", "").strip()
        self.rapidapi_key = rapidapi_key.strip() or os.getenv("RAPIDAPI_KEY", "").strip()
        self.rapidapi_host = rapidapi_host.strip() or os.getenv("RAPIDAPI_HOST", "free-chatgpt-api.p.rapidapi.com").strip()
        self.gemini_client = genai.Client(api_key=self.gemini_key) if self.gemini_key else None

    def execute_agent_prompt(
        self,
        prompt: str,
        location_id: str,
        access_token: str,
        model_name: str = "gemini-3.6-flash",
        history: Optional[List[Dict[str, str]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Processes prompt via Gemini, Groq Cloud, or RapidAPI, determines tool calls, executes GHL API commands, and yields SSE stream updates.
        Supports multimodal attachments (images, PDFs, documents, code).
        """
        provider = detect_provider(model_name)
        ghl = GHLSubAccountClient(location_id=location_id, access_token=access_token)
        
        # Check connection status with in-memory cache (5 min TTL) to avoid hitting GHL API on every message
        if location_id and access_token:
            import time as _t
            cache_key = f"{location_id}:{access_token[:8]}"
            if not hasattr(self, '_conn_cache'):
                self._conn_cache = {}
            cached = self._conn_cache.get(cache_key)
            if cached and (_t.time() - cached["ts"]) < 300:
                conn_status = cached["result"]
            else:
                conn_status = ghl.verify_connection()
                self._conn_cache[cache_key] = {"result": conn_status, "ts": _t.time()}
            if not conn_status.get("success"):
                yield {"type": "tool_start", "name": "verify_connection", "args": {"location_id": location_id}}
                yield {"type": "tool_result", "name": "verify_connection", "result": conn_status}
                yield {"type": "chunk", "text": f"⚠️ **GHL Connection Error:** {conn_status.get('message')}"}
                return

        is_ghl_connected = bool(location_id and access_token)

        # Classify prompt intent for adaptive configuration
        intent = classify_prompt_intent(prompt)
        logger.info(f"Prompt intent classified as: {intent} | Provider: {provider} | Model: {model_name} | Attachments: {len(attachments or [])}")

        # Build adaptive system prompt based on intent, provider, and portfolio context
        system_instruction = self._build_system_prompt(intent, provider, is_ghl_connected, location_id, prompt=prompt)

        if provider == "gemini":
            yield from self._execute_gemini(
                prompt=prompt,
                ghl=ghl,
                is_ghl_connected=is_ghl_connected,
                system_instruction=system_instruction,
                model_name=model_name or "gemini-3.6-flash",
                location_id=location_id,
                access_token=access_token,
                history=history,
                intent=intent,
                attachments=attachments
            )
        elif provider == "puter":
            yield from self._execute_puter_backend(
                prompt=prompt,
                ghl=ghl,
                is_ghl_connected=is_ghl_connected,
                system_instruction=system_instruction,
                model_name=model_name or "x-ai/grok-4.6",
                location_id=location_id,
                access_token=access_token,
                history=history,
                intent=intent,
                attachments=attachments
            )
        elif provider == "openrouter":
            from key_pool_manager import openrouter_key_pool
            active_key = openrouter_key_pool.get_active_key() or self.openrouter_key
            yield from self._execute_openai_compatible(
                prompt=prompt,
                ghl=ghl,
                is_ghl_connected=is_ghl_connected,
                system_instruction=system_instruction,
                model_name=model_name or "meta-llama/llama-3.3-70b-instruct",
                api_url="https://openrouter.ai/api/v1/chat/completions",
                api_key=active_key,
                provider_name="OpenRouter Gateway",
                location_id=location_id,
                access_token=access_token,
                history=history,
                intent=intent,
                attachments=attachments
            )
        elif provider == "rapidapi":
            yield from self._execute_rapidapi(
                prompt=prompt,
                system_instruction=system_instruction,
                history=history,
                intent=intent
            )
        else:
            yield from self._execute_openai_compatible(
                prompt=prompt,
                ghl=ghl,
                is_ghl_connected=is_ghl_connected,
                system_instruction=system_instruction,
                model_name=model_name or "groq/compound-mini",
                api_url="https://api.groq.com/openai/v1/chat/completions",
                api_key=self.groq_key,
                provider_name="Groq Cloud",
                location_id=location_id,
                access_token=access_token,
                history=history,
                intent=intent,
                attachments=attachments
            )

    def _execute_puter_backend(
        self,
        prompt: str,
        ghl: GHLSubAccountClient,
        is_ghl_connected: bool,
        system_instruction: str,
        model_name: str,
        location_id: str,
        access_token: str,
        history: Optional[List[Dict[str, str]]] = None,
        intent: str = "quick_answer",
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Handles backend calls for Puter AI xAI Grok 4.6.
        When called via backend API, tries OpenRouter with active key pool.
        If OpenRouter is depleted, rate-limited, or out of credits, seamlessly bridges to Gemini 3.6 Flash.
        """
        from key_pool_manager import openrouter_key_pool
        active_key = openrouter_key_pool.get_active_key() or self.openrouter_key
        
        has_generated_real_content = False
        if active_key:
            generator = self._execute_openai_compatible(
                prompt=prompt,
                ghl=ghl,
                is_ghl_connected=is_ghl_connected,
                system_instruction=system_instruction,
                model_name="x-ai/grok-4.6",
                api_url="https://openrouter.ai/api/v1/chat/completions",
                api_key=active_key,
                provider_name="OpenRouter (xAI Grok 4.6)",
                location_id=location_id,
                access_token=access_token,
                history=history,
                intent=intent,
                attachments=attachments
            )
            try:
                first_chunk = next(generator, None)
                if first_chunk:
                    chunk_text = first_chunk.get("text", "")
                    if "System Notice: Unable to Generate Response" in chunk_text:
                        logger.warning("OpenRouter failed with error banner. Falling back immediately to Gemini 3.6 Flash...")
                        has_generated_real_content = False
                    else:
                        has_generated_real_content = True
                        yield first_chunk
                        for chunk in generator:
                            yield chunk
                        return
            except Exception as e:
                logger.warning(f"OpenRouter exception: {e}. Falling back to Gemini...")
                has_generated_real_content = False

        if not has_generated_real_content:
            logger.info("Routing Puter Grok request to Gemini 3.6 Flash fallback...")
            yield {
                "type": "chunk",
                "text": "> ℹ️ *Note: xAI Grok 4.6 upstream capacity is busy. Seamlessly routed via **✨ Gemini 3.6 Flash (5-Key Multi-Key Pool)**:*\n\n---\n\n"
            }
            yield from self._execute_gemini(
                prompt=prompt,
                ghl=ghl,
                is_ghl_connected=is_ghl_connected,
                system_instruction=system_instruction,
                model_name="gemini-3.6-flash",
                location_id=location_id,
                access_token=access_token,
                history=history,
                intent=intent,
                attachments=attachments
            )

    def _execute_rapidapi(
        self,
        prompt: str,
        system_instruction: str,
        history: Optional[List[Dict[str, str]]] = None,
        intent: str = "quick_answer"
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Executes prompt via RapidAPI Free ChatGPT endpoint with token streaming.
        """
        if not self.rapidapi_key:
            yield {"type": "chunk", "text": format_friendly_error_banner("RapidAPI Key missing.")}
            return

        url = f"https://{self.rapidapi_host}/chat-completion-one"
        headers = {
            "x-rapidapi-key": self.rapidapi_key,
            "x-rapidapi-host": self.rapidapi_host
        }
        # Compact system header so user's prompt gets maximum available character budget
        concise_sys = "You are an expert GoHighLevel CRM & Funnel Technical Copilot. Provide direct, high-quality, practical answers."
        full_query = f"{concise_sys}\n\nUser Request:\n{prompt}"
        params = {"prompt": full_query[:4000]}

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=45)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    raw_text = data.get("response") or data.get("text") or data.get("result") or str(data)
                except Exception:
                    raw_text = resp.text

                yield from stream_text_tokens(raw_text)
            elif resp.status_code == 403:
                yield {
                    "type": "chunk",
                    "text": (
                        "> ⚠️ **RapidAPI Notice (403 Forbidden):**\n"
                        ">\n"
                        "> `You are not subscribed to this API.`\n"
                        ">\n"
                        "> 💡 **To activate this endpoint on your RapidAPI account:**\n"
                        "> 1. Open the [Free ChatGPT API on RapidAPI](https://rapidapi.com/chatgpt-api-chatgpt-api-default/api/free-chatgpt-api).\n"
                        "> 2. Click the **'Pricing'** tab and click **'Subscribe'** on the Free plan ($0/mo).\n"
                        "> 3. Once subscribed, RapidAPI will authorize your key instantly!"
                    )
                }
            else:
                yield {"type": "chunk", "text": f"⚠️ **RapidAPI Error ({resp.status_code}):** {resp.text}"}
        except Exception as e:
            logger.error(f"RapidAPI request failed: {e}")
            yield {"type": "chunk", "text": format_friendly_error_banner(str(e))}

    def _build_system_prompt(self, intent: str, provider: str, is_ghl_connected: bool, location_id: str, prompt: str = "") -> str:
        """
        Builds an adaptive system prompt implementing the Complete 29 Senior GHL Solutions Architect & SaaS Engineering Rules.
        Anchored in senior-level architectural accuracy, failure-mode awareness, honesty over confidence,
        zero fabrication, strict query scope, and verified agency portfolio knowledge.
        """
        portfolio_proof_block = ""
        p_lower = prompt.lower() if prompt else ""
        # Only inject portfolio case studies if the user explicitly asks about past dashboards, KPI, Meta, or case studies
        if any(kw in p_lower for kw in ["case study", "portfolio", "past project", "custom application", "have you built on top", "facebook analytics", "kpi report", "dashboard example", "pandacare", "xortlogix"]):
            try:
                portfolio_proof_block = agency_portfolio_kb.get_portfolio_context_for_prompt(prompt)
            except Exception as e_kb:
                logger.debug(f"Portfolio context lookup failed: {e_kb}")

        base_prompt = f"""# SYSTEM PROMPT — GOHIGHLEVEL (GHL) TECHNICAL EXPERT & SAAS COPILOT

You are a precise, senior-level GoHighLevel (GHL) Technical Expert and Automation Engineer.
DIRECT WRITING STYLE MANDATE:
- NEVER introduce yourself or your persona.
- NEVER start responses with phrases like "As a Senior GoHighLevel...", "I am excited to discuss...", or "I've had the privilege of...".
- NEVER use marketing buzzwords or unverified experience claims like "seasoned", "extensive experience", "numerous projects", or "expert".
- Answer immediately, directly, concisely, and honestly.
- Accuracy > Honesty > Practical Implementation > Completeness > Impressive-Looking Output.

{portfolio_proof_block}
"""

        base_rules = """1. KEEP CORRECT INFORMATION:
   - If the answer is technically correct, keep it.
   - Give practical, concise instructions.
   - Clearly distinguish GHL-native features from custom/API solutions.

2. NEVER INVENT GHL INFORMATION:
   - Only state platform features and settings that are confirmed.
   - Never present unverified or estimated details as permanent guarantees.

3. FOR API & AUTHENTICATION ANSWERS:
   - Base URL: `https://services.leadconnectorhq.com/` | Version Header: `Version: 2021-07-28`.
   - Clearly distinguish Location Private Integration Bearer Tokens from Marketplace OAuth 2.0.

4. CRM CONTACT PAYLOAD HYGIENE & STRICT E.164 PHONE STANDARDS:
   - When `firstName` and `lastName` are provided, do NOT include a redundant `name` property.
   - All phone numbers in examples MUST be strictly valid E.164 format (+1 followed by 10 digits).

5. ZERO DUPLICATION & SINGLE-PASS DELIVERY:
   - NEVER repeat the same solution, payload, or endpoint twice in a single response.
"""

        tool_block = ""
        if is_ghl_connected:
            tool_block = f"""
=============================================================================
AUTONOMOUS GHL API TOOL EXECUTION
=============================================================================
- Sub-Account Location ID ({location_id}) is connected.
- When the user asks you to create or configure assets directly in their HighLevel sub-account, invoke the native tools (`create_contact`, `create_pipeline`, `create_tag`, `create_custom_field`, `create_opportunity`, etc.).
"""

        # Direct Q&A, Job Proposals, Consultations, or Direct Asset Commands
        if intent == "quick_answer":
            return base_prompt + f"""
=============================================================================
MANDATORY GOHIGHLEVEL (GHL) OPERATIONAL RULES
=============================================================================
{base_rules}
8. STRICT RESPONSE SCOPE & NO UNSOLICITED EXPANSION:
   - Answer ONLY what the prospect explicitly asks for.
   - Once the user's questions are completely answered, STOP IMMEDIATELY.
   - NEVER automatically append unrequested:
     • Technical checklists
     • Implementation agendas
     • DNS instructions (e.g. CNAME targets)
     • Asset requirement lists
     • Testing protocols
     • Setup steps / tutorials
   - The response should feel like a natural, concise human reply, NOT an unprompted technical specification.

=============================================================================
TASK DIRECTIVE: DIRECT ANSWER, PROPOSAL & STRICT QUERY RELEVANCE
=============================================================================
- Answer ONLY what the user explicitly asks for.
- NO UNSOLICITED EXPANSION: Once the questions are answered, STOP IMMEDIATELY. DO NOT append checklists, agendas, DNS guides, or testing protocols.
- FOR JOB PROPOSALS / RFPs / CLIENT CONSULTATION QUERIES:
  • ZERO FLUFF OPENING: DO NOT write "As a Senior GoHighLevel...", "I've had the privilege of working on numerous projects...", or "I am excited to discuss...".
  • EXACT CLEAN STRUCTURE:
    If the prompt asks for a "DONE WITH YOU" proposal or co-building proposal on Zoom:
    - Start immediately with:
      DONE WITH YOU — I would be glad to build your membership portal with you live on Zoom.

      To answer your questions directly:

      • **Portals built:** I don't have a verified portal count on file, so I won't give you a made-up number. My verified GHL experience includes membership products, offers, lesson structuring, custom CNAME domains, and automated access workflows.
      • **Approach on Zoom:** We’ll co-build the portal live through screen sharing. I’ll configure it in your sub-account, explain the relevant settings as we go, test the member login and access flow together, and make adjustments in real time.
      • **Availability:** I can coordinate a mutually convenient Zoom schedule based on your preferred time zone and session hours.

      The goal is not only to build the portal, but also to ensure you understand how it works and can manage it independently afterward.
  • STOP IMMEDIATELY after the closing sentence. DO NOT append checklists, DNS instructions, or implementation agendas.
{tool_block}
"""

        if intent == "iteration":
            return base_prompt + f"""
=============================================================================
MANDATORY GOHIGHLEVEL (GHL) OPERATIONAL RULES
=============================================================================
{base_rules}
=============================================================================
TASK DIRECTIVE: DOCUMENT EDITING, DESIGN REFINEMENT & CHANGE LOG
=============================================================================
The user is providing an existing codebase, funnel, landing page, or document (either in chat or as an attached file like `landing_page.html`) and requesting specific changes (e.g. colors, visual styling, layout tweaks, copy adjustments, or feature additions).

YOUR INSTRUCTIONS:
1. IMPLEMENT THE REQUESTED CHANGES DIRECTLY into the code or document provided by the user.
   • If the user requests color/design changes, apply the new color palette throughout the CSS and components (backgrounds, text gradients, borders, buttons, cards).
   • Maintain 100% of the working logic (navigation, forms, validation, and functionality) unless specifically asked to change it.
   • Ensure the updated code is production-ready and fully contained.

2. STRUCTURE YOUR RESPONSE IN TWO DISTINCT PARTS:

   PART 1: UPDATED CODE / DOCUMENT
   • Provide the fully updated, revised code inside a clean code block (e.g. ```html ... ```).

   PART 2: SUMMARY OF CHANGES MADE (What Was Changed)
   • Provide a clear, bullet-pointed summary explaining EXACTLY what changes were made in the code/design:
     - **Color Palette & Design Updates:** List the exact colors/shades updated (e.g. Old theme vs New theme).
     - **Component / Styling Adjustments:** List buttons, typography, cards, or hero elements modified.
     - **Functional / Structural Changes (if requested):** Note any new sections, forms, or steps added or updated.
   • If the user asked for changes in non-code elements (such as workflows, tags, or copy), explain those specific changes clearly and concisely.
   • DO NOT generate unrequested 14-section CRM architectures or redundant tables. Focus strictly on delivering the updated code/document and explaining the modifications made.
{tool_block}
"""

        # For full_build: ALWAYS deliver complete code block first followed by full CRM architecture
        # DYNAMIC: Extract brand/industry context from the user's prompt instead of hardcoding
        return base_prompt + f"""
{base_rules}
=============================================================================
TASK DIRECTIVE: COMPLETE PRODUCTION ARCHITECTURE & FULL CODE BUILD
=============================================================================
You are a Lead GoHighLevel Solutions Architect. The user is requesting a FULL PRODUCTION BUILD.

CRITICAL IDENTITY & ENTITY PRESERVATION RULE:
- You MUST extract and preserve the exact business name, industry, offers, pricing, taglines, and colors from the user's prompt.
- NEVER replace the user's business (e.g. Mastermind Coaching Academy) with a generic or different business (e.g. Apex Home Solutions, Gym, Real Estate).
- ALL copy, headlines, prices, steps, and themes MUST match the user's prompt 100%.

Output all 5 sections in this exact order with ZERO preamble text:

1. Complete Single-File HTML App (```html <!DOCTYPE html> ... </html>```)
   • Use Tailwind CSS CDN (`<script src="https://cdn.tailwindcss.com"></script>`) with utility classes.
   • ALL funnel steps MUST be fully built inside this ONE file with interactive JavaScript tab navigation (`switchStep(n)`).
   • Fully build EVERY step with real high-converting copy, real inputs, real CTA buttons:
     - Step 1: Opt-In (Hero, benefit bullets, lead form with real client-side validation for name, email, and valid E.164 phone).
     - Step 2: VSL Video Room (Real `<video>` element or custom HTML5 player with play/pause controls, real `timeupdate` event listener in JavaScript that computes exact percentage watched, and fires an event at 80% mark to trigger the CTA and log the progress).
     - Step 3: TRUE 2-Step Order Form (NOT just one form!):
       * SUB-STEP 1: Contact Details (First Name, Last Name, Email, Phone). Clicking "Continue to Payment" validates all 4 inputs, triggers the Cart Abandonment event/webhook, and reveals Sub-Step 2.
       * SUB-STEP 2: Payment & Card Details (Card Number, Expiry, CVC, Zip code) with REAL client-side input validation (Luhn/16-digit check, expiry check, CVC check — if empty or invalid, show error and BLOCK checkout; do NOT allow empty checkout). Include order summary with itemized core price + toggleable Bump Offer checkbox that updates total in real time.
     - Step 4: OTO Upsell Page (Urgency banner, value stack, 1-click accept button that simulates tokenized secondary charge with loading spinner + explicit "No thanks" bypass link).
     - Step 5: Thank You Page (Access credentials notice, instant onboarding schedule calendar embed placeholder, community link).
   • Code MUST be 100% complete and self-contained from `<!DOCTYPE html>` to `</html>` without truncation or placeholders.

2. Funnel Step Map & URLs (Compact Markdown Table)
   • Columns: Step # | Step Name | Path/Slug | Page Type | Primary CTA / Action | Next Step Trigger

3. HighLevel Pipeline Stages, Custom Fields & Tags (Compact Markdown Tables)
   • Pipeline Stages: Order | Stage Name | Exact Entry Trigger | Exit / Win Condition
   • Contact Custom Fields: Field Name | Unique Key | Data Type | Implementation Note (Detail how client-side JS sends VSL watch progress via GHL Custom Inbound Webhook)
   • Contact Tags Taxonomy: Tag Name | Exact Application Trigger | Removal Trigger
   • Magic Link Security Architecture: Detail signed query parameters (`?token={{ contact.access_token }}&cid={{ contact.id }}`) validated via GHL custom value / webhook, not unauthenticated raw contact IDs.

4. Production-Ready HighLevel Workflow Automations (Separate, Clean Workflows)
   DO NOT mix lead follow-up and cart recovery into one vague text block. Provide complete, fully specified workflows with exact timings, if/else branch logic, and full SMS/Email copy:
   • WORKFLOW 1: Instant VSL Access & Lead Delivery (Trigger, Opportunity stage, SMS + Email copy)
   • WORKFLOW 2: 24-Hour Evergreen VSL Replay & Urgency Cadence (Lead Recovery: Wait 2h, Wait 6h, Wait 16h with exact copy)
   • WORKFLOW 3: 2-Step Order Form Cart Abandonment Sequence (Cart Recovery: T+15m, T+4h, T+24h with core purchase stop-checks)
   • WORKFLOW 4: Core Purchase & OTO Fulfillment (Payment triggers for exact core price and exact OTO price, tag management, custom fields)
   • WORKFLOW 5: Dual-Event Onboarding Activation (Appointment Confirmed + Portal Access)

5. Post-Funnel Implementation & Deployment Walkthrough
   • Provide the user with a clear, step-by-step technical implementation guide explaining:
     - How to import this single-file funnel into GoHighLevel (Custom Code / HTML element vs Funnel Builder).
     - How to connect Stripe in HighLevel Sub-Account (Settings ➔ Payments ➔ Integrations).
     - How to set up the Inbound Webhook for VSL 80% watch tracking.
     - How to test the 2-step order form and verify cart abandonment in HighLevel.

DO NOT output bracketed tags like `[RECOMMENDED]`, `[VERIFIED]`.
{tool_block}
"""

    def _execute_gemini(
        self,
        prompt: str,
        ghl: GHLSubAccountClient,
        is_ghl_connected: bool,
        system_instruction: str,
        model_name: str,
        location_id: str,
        access_token: str,
        history: Optional[List[Dict[str, str]]] = None,
        intent: str = "quick_answer",
        is_fallback: bool = False,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        from key_pool_manager import gemini_key_pool
        active_gemini_key = gemini_key_pool.get_active_key() or self.gemini_key
        if not active_gemini_key:
            yield {"type": "chunk", "text": "⚠️ **Error:** Gemini API Key is not configured on server."}
            return

        candidate_models = [model_name]
        for m in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.7-flash", "gemini-flash-latest"]:
            if m not in candidate_models:
                candidate_models.append(m)

        # Process attachments (images & documents)
        augmented_prompt, image_items = process_attachments_for_prompt(prompt, attachments)

        # Build conversation contents with intelligent history compression
        compressed_history = compress_history(history or [], "gemini", max_messages=8, intent=intent)
        contents = []
        for msg in compressed_history:
            role = "user" if msg.get("role") == "user" else "model"
            text = msg.get("content", "").strip()
            if text:
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))
        
        # Build user turn with text and decoded image parts
        user_parts = [types.Part.from_text(text=augmented_prompt)]
        for img in image_items:
            img_data = img.get("data", "")
            img_mime = img.get("mime_type", "image/jpeg") or "image/jpeg"
            if "," in img_data:
                img_data = img_data.split(",", 1)[1]
            try:
                raw_bytes = base64.b64decode(img_data)
                user_parts.append(types.Part.from_bytes(data=raw_bytes, mime_type=img_mime))
            except Exception as e_img:
                logger.warning(f"Failed to decode image attachment {img.get('name')}: {e_img}")

        contents.append(types.Content(role="user", parts=user_parts))

        # Adaptive temperature and token budget based on intent
        temp = get_temperature(intent, is_tool_mode=is_ghl_connected)
        max_toks = get_token_budget("gemini", intent)
        thinking_toks = get_thinking_budget(intent)

        # Instant Direct Streaming Mode when autonomous GHL tools are not executing
        if not is_ghl_connected:
            stream_started = False
            last_err_text = ""
            accumulated_text = ""
            
            num_keys = len(gemini_key_pool.keys_state) or 1
            for key_attempt in range(num_keys):
                active_gemini_key = gemini_key_pool.get_active_key() or self.gemini_key
                if not active_gemini_key:
                    break
                current_client = genai.Client(api_key=active_gemini_key)

                for mod in candidate_models:
                    try:
                        config_args = {
                            "system_instruction": system_instruction,
                            "temperature": temp,
                            "max_output_tokens": max_toks
                        }
                        if "3.7" in mod or "think" in mod:
                            try:
                                config_args["thinking_config"] = types.ThinkingConfig(thinking_budget=thinking_toks)
                            except Exception:
                                pass

                        response_stream = current_client.models.generate_content_stream(
                            model=mod,
                            contents=contents,
                            config=types.GenerateContentConfig(**config_args)
                        )
                        for chunk in response_stream:
                            if chunk.text:
                                stream_started = True
                                accumulated_text += chunk.text
                                yield {"type": "chunk", "text": chunk.text}

                        # Multi-Pass Seamless Auto-Continuation for Gemini
                        max_gemini_cont = 3
                        while stream_started and detect_truncation(accumulated_text) and max_gemini_cont > 0:
                            max_gemini_cont -= 1
                            logger.info(f"Gemini output truncated (len={len(accumulated_text)}). Auto-triggering seamless continuation {3 - max_gemini_cont}/3...")
                            try:
                                recent_tail = accumulated_text[-2400:]
                                last_cutoff = accumulated_text[-80:].replace('\n', ' ')
                                if intent == "iteration":
                                    cont_user_msg = f"Continue EXACTLY from: '{last_cutoff}'. Do NOT repeat any previous text. Finish all remaining code and then output the complete 'SUMMARY OF CHANGES MADE' section."
                                else:
                                    cont_user_msg = f"Continue EXACTLY from: '{last_cutoff}'. Do NOT repeat any previous text. Finish all remaining HTML tags, then output the complete Funnel Step Map, HighLevel Pipeline Stages & Custom Fields tables, and all 5 Workflows in full detail."

                                cont_contents = [
                                    types.Content(role="model", parts=[types.Part.from_text(text=recent_tail)]),
                                    types.Content(role="user", parts=[types.Part.from_text(text=cont_user_msg)])
                                ]
                                cont_config = {
                                    "temperature": temp,
                                    "max_output_tokens": max_toks
                                }
                                cont_stream = current_client.models.generate_content_stream(
                                    model=mod,
                                    contents=cont_contents,
                                    config=types.GenerateContentConfig(**cont_config)
                                )
                                for c_chunk in cont_stream:
                                    if c_chunk.text:
                                        accumulated_text += c_chunk.text
                                        yield {"type": "chunk", "text": c_chunk.text}
                            except Exception as e_cont:
                                logger.warning(f"Gemini auto-continuation error on key {active_gemini_key[:8]}: {e_cont}")
                                if "429" in str(e_cont) or "RESOURCE_EXHAUSTED" in str(e_cont):
                                    gemini_key_pool.mark_key_depleted(active_gemini_key, 429, str(e_cont))
                                break

                        # Check if genuinely truncated after Gemini loop exhausted (at least 1000 chars generated)
                        if stream_started and len(accumulated_text) > 1000 and detect_truncation(accumulated_text) and not is_fallback and self.groq_key:
                            recent_tail = accumulated_text[-2000:]
                            last_cutoff = accumulated_text[-80:].replace('\n', ' ')
                            logger.info(f"Gemini capacity reached mid-generation. Handing off to Groq Cloud...")
                            yield {
                                "type": "chunk",
                                "text": f"\n\n> 🔄 **Model Handover:** Google Gemini generated the initial architecture ({len(accumulated_text):,} chars). Reaching quota limit — **Groq Cloud (Qwen 3.8)** is now seamlessly continuing generation from this exact point...\n\n---\n\n"
                            }
                            yield from self._execute_openai_compatible(
                                prompt=prompt,
                                ghl=ghl,
                                is_ghl_connected=is_ghl_connected,
                                system_instruction=system_instruction,
                                model_name="qwen/qwen3.8-27b",
                                api_url="https://api.groq.com/openai/v1/chat/completions",
                                api_key=self.groq_key,
                                provider_name="Groq Cloud",
                                location_id=location_id,
                                access_token=access_token,
                                history=history,
                                intent=intent,
                                is_fallback=True,
                                attachments=attachments,
                                continuation_tail=recent_tail,
                                continuation_cutoff=last_cutoff
                            )
                            return

                        if accumulated_text.count('```') % 2 != 0:
                            yield {"type": "chunk", "text": "\n```\n"}

                        gemini_key_pool.record_success(active_gemini_key)
                        return
                    except Exception as e_mod:
                        last_err_text = str(e_mod)
                        logger.warning(f"Gemini streaming with {mod} on key {active_gemini_key[:8]} failed: {e_mod}")
                        if "429" in last_err_text or "RESOURCE_EXHAUSTED" in last_err_text or "quota" in last_err_text.lower():
                            gemini_key_pool.mark_key_depleted(active_gemini_key, 429, last_err_text)

                        # If text was already started and errored out, seamlessly hand over to Groq
                        if stream_started and not is_fallback and self.groq_key:
                            recent_tail = accumulated_text[-2000:]
                            last_cutoff = accumulated_text[-80:].replace('\n', ' ')
                            yield {
                                "type": "chunk",
                                "text": f"\n\n> 🔄 **Model Handover:** Google Gemini limit reached ({len(accumulated_text):,} chars generated). Seamlessly continuing with **Groq Cloud (Qwen 3.8)**...\n\n---\n\n"
                            }
                            yield from self._execute_openai_compatible(
                                prompt=prompt,
                                ghl=ghl,
                                is_ghl_connected=is_ghl_connected,
                                system_instruction=system_instruction,
                                model_name="qwen/qwen3.8-27b",
                                api_url="https://api.groq.com/openai/v1/chat/completions",
                                api_key=self.groq_key,
                                provider_name="Groq Cloud",
                                location_id=location_id,
                                access_token=access_token,
                                history=history,
                                intent=intent,
                                is_fallback=True,
                                attachments=attachments,
                                continuation_tail=recent_tail,
                                continuation_cutoff=last_cutoff
                            )
                            return

                        if stream_started:
                            return

                        if "pro" in mod.lower() or "3.7" in mod.lower():
                            continue

            # Failover logic: Groq Cloud first (verified available), then OpenRouter
            if not is_fallback:
                if self.groq_key:
                    groq_target = "qwen/qwen3.8-27b"
                    logger.info("Falling back from Gemini to Groq Cloud before start...")
                    yield {
                        "type": "chunk",
                        "text": "> 🔄 **Model Handover:** Google Gemini active keys busy or at quota. Routing query to **Groq Cloud (Qwen 3.8)** for instant generation...\n\n---\n\n"
                    }
                    yield from self._execute_openai_compatible(
                        prompt=prompt,
                        ghl=ghl,
                        is_ghl_connected=is_ghl_connected,
                        system_instruction=system_instruction,
                        model_name=groq_target,
                        api_url="https://api.groq.com/openai/v1/chat/completions",
                        api_key=self.groq_key,
                        provider_name="Groq Cloud",
                        location_id=location_id,
                        access_token=access_token,
                        history=history,
                        intent=intent,
                        is_fallback=True,
                        attachments=attachments
                    )
                    return

            if "429" in last_err_text or "RESOURCE_EXHAUSTED" in last_err_text or "quota" in last_err_text.lower():
                yield {"type": "chunk", "text": "⚠️ **Rate Limit Exceeded:** Google Gemini API quota is exhausted. Please wait ~15-30 seconds or switch models in the selector."}
            else:
                yield {"type": "chunk", "text": f"⚠️ **Service Notice:** Google Gemini is temporarily unavailable ({last_err_text[:120] if last_err_text else 'busy'}). Please retry in a few moments."}
            return

        # Tool Execution Mode when GHL is connected
        response = None
        last_exception = None

        for mod in candidate_models:
            try:
                config_args = {
                    "system_instruction": system_instruction,
                    "temperature": 0.1,
                    "max_output_tokens": 8192,
                    "tools": [{"function_declarations": GHL_TOOLS_DECLARATIONS}]
                }
                if "3.7" in mod or "think" in mod:
                    try:
                        config_args["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
                    except Exception:
                        pass

                response = self.gemini_client.models.generate_content(
                    model=mod,
                    contents=contents,
                    config=types.GenerateContentConfig(**config_args)
                )
                last_exception = None
                break
            except Exception as e_mod:
                last_exception = e_mod
                logger.warning(f"Gemini model {mod} failed: {e_mod}, trying next fallback...")

        if response is None or last_exception is not None:
            # Fallback for tool execution: OpenRouter first, then Groq
            if self.openrouter_key:
                from key_pool_manager import openrouter_key_pool
                pool_key = openrouter_key_pool.get_active_key()
                if pool_key:
                    yield from self._execute_openai_compatible(
                        prompt=prompt,
                        ghl=ghl,
                        is_ghl_connected=is_ghl_connected,
                        system_instruction=system_instruction,
                        model_name="meta-llama/llama-3.3-70b-instruct",
                        api_url="https://openrouter.ai/api/v1/chat/completions",
                        api_key=pool_key,
                        provider_name="OpenRouter",
                        location_id=location_id,
                        access_token=access_token,
                        history=history,
                        intent=intent,
                        is_fallback=True
                    )
                    return
            if self.groq_key:
                yield from self._execute_openai_compatible(
                    prompt=prompt,
                    ghl=ghl,
                    is_ghl_connected=is_ghl_connected,
                    system_instruction=system_instruction,
                    model_name="qwen/qwen3.8-27b",
                    api_url="https://api.groq.com/openai/v1/chat/completions",
                    api_key=self.groq_key,
                    provider_name="Groq Cloud",
                    location_id=location_id,
                    access_token=access_token,
                    history=history,
                    intent=intent,
                    attachments=attachments,
                    is_fallback=True
                )
                return
            yield {"type": "chunk", "text": format_friendly_error_banner(str(last_exception))}
            return

        try:
            function_calls = response.function_calls or []
            if function_calls:
                tool_results_summary = []
                for fc in function_calls:
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}

                    yield {"type": "tool_start", "name": tool_name, "args": tool_args}
                    result = self._dispatch_tool_call(ghl, tool_name, tool_args, location_id, access_token)
                    yield {"type": "tool_result", "name": tool_name, "result": result}

                    msg = result.get("message") or result.get("error") or json.dumps(result)
                    tool_results_summary.append(f"Tool `{tool_name}` result: {msg}")

                synthesis_prompt = f"User Request: {prompt}\n\nActions Taken:\n" + "\n".join(tool_results_summary) + "\n\nProvide a friendly final response confirming the action taken in the GHL Sub-Account."
                synth_text = "Action execution complete."
                for mod in candidate_models:
                    try:
                        synth_res = self.gemini_client.models.generate_content(
                            model=mod,
                            contents=synthesis_prompt
                        )
                        if synth_res and synth_res.text:
                            synth_text = synth_res.text
                            break
                    except Exception:
                        pass

                yield from stream_text_tokens(synth_text)
            else:
                full_reply = response.text or "How can I assist you with your GHL Sub-Account?"
                yield from stream_text_tokens(full_reply)

        except Exception as e:
            logger.error(f"Gemini execution error: {e}", exc_info=True)
            yield {"type": "chunk", "text": format_friendly_error_banner(str(e))}

    def _execute_openai_compatible(
        self,
        prompt: str,
        ghl: GHLSubAccountClient,
        is_ghl_connected: bool,
        system_instruction: str,
        model_name: str,
        api_url: str,
        api_key: str,
        provider_name: str,
        location_id: str,
        access_token: str,
        history: Optional[List[Dict[str, str]]] = None,
        intent: str = "quick_answer",
        is_fallback: bool = False,
        extra_headers: Optional[Dict[str, str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        continuation_tail: str = "",
        continuation_cutoff: str = ""
    ) -> Generator[Dict[str, Any], None, None]:
        is_openrouter = ("openrouter" in provider_name.lower())
        active_key = api_key
        if is_openrouter:
            from key_pool_manager import openrouter_key_pool
            pool_key = openrouter_key_pool.get_active_key()
            if pool_key:
                active_key = pool_key

        if not active_key:
            yield {"type": "chunk", "text": format_friendly_error_banner(f"{provider_name} API Key missing")}
            return

        headers = {
            "Authorization": f"Bearer {active_key}",
            "Content-Type": "application/json"
        }
        if extra_headers:
            headers.update(extra_headers)

        messages = [
            {"role": "system", "content": system_instruction}
        ]

        # Process attachments (images & documents)
        augmented_prompt, image_items = process_attachments_for_prompt(prompt, attachments)

        # Hard mandate for Groq models to ensure raw code is always printed
        if any(kw in prompt.lower() for kw in ['html', 'css', 'code', 'checkout', 'funnel', 'landing page', 'page', 'form']):
            messages[0]["content"] += (
                "\n\n=============================================================================\n"
                "CRITICAL SINGLE-FILE APPLICATION MANDATE:\n"
                "You MUST output ONE complete, 100% production-ready ```html <!DOCTYPE html> ... </html>``` code block "
                "containing ALL 5 steps inside this single file (#step-optin, #step-vsl, #step-checkout, #step-upsell, #step-thankyou) "
                "with interactive JavaScript tab navigation.\n"
                "DO NOT split into 5 separate boilerplate HTML files with duplicate <!DOCTYPE html> headers. "
                "Use Tailwind CDN utilities (<script src=\"https://cdn.tailwindcss.com\"></script>) directly on elements without manual CSS stylesheets. "
                "Guarantee the code completes 100% from <!DOCTYPE html> down to </html>."
            )

        # If continuing from a previous model's cutoff, prime messages to resume cleanly
        if continuation_tail and continuation_cutoff:
            messages.append({"role": "user", "content": augmented_prompt})
            messages.append({"role": "assistant", "content": f"...{continuation_tail}"})
            messages.append({
                "role": "user",
                "content": f"The response was interrupted at: '{continuation_cutoff}'. Continue generating EXACTLY from that point onward without repeating any previously outputted text. Finish all remaining HTML tags, tables, and workflows completely."
            })
        else:
            # Compress conversation history intelligently
            provider_slug = "groq" if "groq" in provider_name.lower() else "openrouter"
            compressed_history = compress_history(history or [], provider_slug, max_messages=4, intent=intent)
            for msg in compressed_history:
                role = "user" if msg.get("role") == "user" else "assistant"
                content = msg.get("content", "").strip()
                if content:
                    messages.append({"role": role, "content": content})
            
            messages.append({"role": "user", "content": augmented_prompt})

        # Adaptive token budget and temperature
        target_max_tokens = get_token_budget("openrouter" if is_openrouter else "groq", intent)
        if is_openrouter:
            target_max_tokens = min(target_max_tokens, 1200)
        target_temp = get_temperature(intent, is_tool_mode=is_ghl_connected)

        # Validate Groq model name when calling Groq
        if not is_openrouter:
            valid_groq_models = ["groq/compound-mini", "groq/compound", "qwen/qwen3.8-27b", "qwen/qwen3.6-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "allam-2-7b"]
            if model_name not in valid_groq_models:
                model_name = "groq/compound-mini"

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": target_temp,
            "max_tokens": target_max_tokens
        }

        # Find if model supports tools
        model_meta = next((m for m in MODELS_CATALOG if m["id"] == model_name), None)
        can_call_tools = is_ghl_connected and (model_meta.get("supports_tools", True) if model_meta else True)

        if can_call_tools:
            payload["tools"] = get_openai_tools_schema()
            payload["tool_choice"] = "auto"
        else:
            payload["stream"] = True

        try:
            resp = requests.post(api_url, headers=headers, json=payload, stream=(not can_call_tools), timeout=45)
            
            # If OpenRouter returns credit or quota error (401, 402, 429), retry with lower max_tokens or rotate key
            if is_openrouter and resp.status_code in [401, 402, 429]:
                # Try with 500 max_tokens if 402 was due to upfront token credit limit
                if resp.status_code == 402 and payload.get("max_tokens", 1000) > 500:
                    logger.info("OpenRouter 402 credit cap hit. Retrying with reduced max_tokens=500...")
                    payload["max_tokens"] = 500
                    resp = requests.post(api_url, headers=headers, json=payload, stream=(not can_call_tools), timeout=45)

                if resp.status_code in [401, 402, 429]:
                    from key_pool_manager import openrouter_key_pool
                    openrouter_key_pool.mark_key_depleted(active_key, resp.status_code, resp.text[:120])
                    next_key = openrouter_key_pool.get_active_key()
                    if next_key and next_key != active_key:
                        logger.info(f"OpenRouter key {active_key[:12]}... depleted/throttled. Shifting to next pool key {next_key[:12]}... and retrying...")
                        headers["Authorization"] = f"Bearer {next_key}"
                        active_key = next_key
                        resp = requests.post(api_url, headers=headers, json=payload, stream=(not can_call_tools), timeout=45)

            # If Groq hits 413 TPM limit, reduce max_tokens and retry
            if not is_openrouter and resp.status_code == 413:
                if payload.get("max_tokens", 5200) > 3200:
                    logger.info("Groq TPM limit hit (413). Retrying with reduced max_tokens=3200...")
                    payload["max_tokens"] = 3200
                    resp = requests.post(api_url, headers=headers, json=payload, stream=(not can_call_tools), timeout=45)

            if resp.status_code != 200:
                err_body = resp.text
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message", err_body)
                except Exception:
                    err_msg = err_body
                
                logger.warning(f"{provider_name} API Error ({resp.status_code}): {err_msg}")
                
            if resp.status_code != 200:
                err_body = resp.text
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message", err_body)
                except Exception:
                    err_msg = err_body
                
                logger.warning(f"Groq API Error ({resp.status_code}): {err_msg}")
                yield {"type": "chunk", "text": format_friendly_error_banner(err_msg)}
                return

            if not can_call_tools:
                # Direct streaming from OpenRouter / Groq SSE stream with Auto-Continuation
                accumulated_text = ""
                finish_reason = None
                for raw_line in resp.iter_lines():
                    if raw_line:
                        line_str = raw_line.decode('utf-8', errors='replace')
                        if line_str.startswith('data: '):
                            payload_str = line_str[6:].strip()
                            if payload_str == '[DONE]':
                                break
                            try:
                                chunk_data = json.loads(payload_str)
                                choice = chunk_data.get('choices', [{}])[0]
                                delta = choice.get('delta', {})
                                content_piece = delta.get('content', '')
                                if choice.get('finish_reason'):
                                    finish_reason = choice.get('finish_reason')
                                if content_piece:
                                    accumulated_text += content_piece
                                    yield {"type": "chunk", "text": content_piece}
                            except Exception:
                                pass

                # Auto-Continuation loop if stream cut off (finish_reason == "length" or unclosed code fence)
                # OPTIMIZED: Don't resend original prompt or system prompt — saves ~800 tokens per continuation
                max_continuations = 3
                while (finish_reason == "length" or detect_truncation(accumulated_text)) and max_continuations > 0:
                    max_continuations -= 1
                    logger.info(f"Auto-continuation triggered for {provider_name} (finish_reason={finish_reason}, len={len(accumulated_text)})")
                    recent_tail = accumulated_text[-2400:]
                    last_cutoff = accumulated_text[-80:].replace('\n', ' ')
                    cont_messages = [
                        {
                            "role": "user",
                            "content": f"The response was cut off at: '{last_cutoff}'.\n\nRecent context:\n```\n...{recent_tail}\n```\n\nContinue generating EXACTLY from that point. Do NOT repeat any previous text. Complete all remaining sections, close all HTML tags, and finish completely."
                        }
                    ]
                    cont_payload = {
                        "model": model_name,
                        "messages": cont_messages,
                        "temperature": target_temp,
                        "max_tokens": target_max_tokens,
                        "stream": True
                    }
                    try:
                        cont_resp = requests.post(api_url, headers=headers, json=cont_payload, stream=True, timeout=45)
                        if cont_resp.status_code == 200:
                            finish_reason = None
                            is_first_chunk = True
                            for c_line in cont_resp.iter_lines():
                                if c_line:
                                    c_str = c_line.decode('utf-8', errors='replace')
                                    if c_str.startswith('data: '):
                                        c_payload = c_str[6:].strip()
                                        if c_payload == '[DONE]':
                                            break
                                        try:
                                            c_data = json.loads(c_payload)
                                            c_choice = c_data.get('choices', [{}])[0]
                                            c_delta = c_choice.get('delta', {})
                                            c_text = c_delta.get('content', '')
                                            if c_choice.get('finish_reason'):
                                                finish_reason = c_choice.get('finish_reason')
                                            if c_text:
                                                if is_first_chunk:
                                                    is_first_chunk = False
                                                    if c_text.startswith("```html\n"):
                                                        c_text = c_text[8:]
                                                    elif c_text.startswith("```\n"):
                                                        c_text = c_text[4:]
                                                accumulated_text += c_text
                                                yield {"type": "chunk", "text": c_text}
                                        except Exception:
                                            pass
                        else:
                            break
                    except Exception as e_cont:
                        logger.warning(f"Continuation request failed: {e_cont}")
                        break

                # If Groq was generating and stopped prematurely, hand off to OpenRouter Multi-Key Pool
                if not is_openrouter and detect_truncation(accumulated_text):
                    from key_pool_manager import openrouter_key_pool
                    openrouter_key = openrouter_key_pool.get_active_key() or self.openrouter_key
                    if openrouter_key:
                        recent_tail = accumulated_text[-2000:]
                        last_cutoff = accumulated_text[-80:].replace('\n', ' ')
                        logger.info("Groq capacity exhausted mid-generation. Handing off to OpenRouter Llama 3.3 70B pool...")
                        yield {
                            "type": "chunk",
                            "text": f"\n\n> 🔄 **Model Handover:** Groq Cloud limit reached ({len(accumulated_text):,} chars generated). Seamlessly continuing with **Llama 3.3 70B (OpenRouter 6-Key Pool)** from this exact point...\n\n---\n\n"
                        }
                        yield from self._execute_openai_compatible(
                            prompt=prompt,
                            ghl=ghl,
                            is_ghl_connected=is_ghl_connected,
                            system_instruction=system_instruction,
                            model_name="meta-llama/llama-3.3-70b-instruct",
                            api_url="https://openrouter.ai/api/v1/chat/completions",
                            api_key=openrouter_key,
                            provider_name="OpenRouter",
                            location_id=location_id,
                            access_token=access_token,
                            history=history,
                            intent=intent,
                            is_fallback=True,
                            attachments=attachments,
                            continuation_tail=recent_tail,
                            continuation_cutoff=last_cutoff
                        )
                        return

                if accumulated_text.count('```') % 2 != 0:
                    yield {"type": "chunk", "text": "\n```\n"}
                return

            data = resp.json()
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            tool_calls = message.get("tool_calls", [])

            if tool_calls and is_ghl_connected:
                messages.append(message)
                tool_results_summary = []

                for tc in tool_calls:
                    fn_data = tc.get("function", {})
                    tool_name = fn_data.get("name", "")
                    raw_args = fn_data.get("arguments", "{}")
                    try:
                        tool_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    except Exception:
                        tool_args = {}

                    yield {
                        "type": "tool_start",
                        "name": tool_name,
                        "args": tool_args
                    }

                    res = self._dispatch_tool_call(ghl, tool_name, tool_args, location_id, access_token)

                    yield {
                        "type": "tool_result",
                        "name": tool_name,
                        "result": res
                    }

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", "call_1"),
                        "content": json.dumps(res)
                    })
                    tool_results_summary.append(f"Tool {tool_name} executed: {res.get('success', False)}")

                # Second turn after tool call
                follow_up_payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": target_max_tokens
                }
                follow_resp = requests.post(api_url, headers=headers, json=follow_up_payload, timeout=45)
                if follow_resp.status_code == 200:
                    follow_data = follow_resp.json()
                    follow_choice = follow_data.get("choices", [{}])[0]
                    final_content = follow_choice.get("message", {}).get("content", "")
                    yield from stream_text_tokens(final_content)
                else:
                    yield {"type": "chunk", "text": "✅ GHL Tool actions executed successfully in your sub-account."}
            else:
                reply_text = message.get("content", "") or "How can I assist you with your GHL Sub-Account?"
                if detect_truncation(reply_text) and intent == "full_build":
                    reply_text += "\n\n---\n> ⚠️ **Notice:** This response reached the model's token limit. For full, untruncated blueprints, select **✨ Gemini 3.6 Flash**."
                yield from stream_text_tokens(reply_text)

        except requests.exceptions.Timeout:
            if self.gemini_client:
                yield {
                    "type": "chunk",
                    "text": f"> ℹ️ **Notice:** {provider_name} server timed out. Automatically switching to **✨ Gemini 3.6 Flash** to complete your request...\n\n---\n\n"
                }
                yield from self._execute_gemini(
                    prompt=prompt,
                    ghl=ghl,
                    is_ghl_connected=is_ghl_connected,
                    system_instruction=system_instruction,
                    model_name="gemini-3.6-flash",
                    location_id=location_id,
                    access_token=access_token,
                    history=history,
                    intent=intent,
                    attachments=attachments
                )
                return
            yield {"type": "chunk", "text": f"⚠️ **Timeout:** {provider_name} server took too long to respond. Please try again."}
        except Exception as e:
            logger.error(f"{provider_name} request failed: {e}", exc_info=True)
            if self.gemini_client:
                yield {
                    "type": "chunk",
                    "text": f"> ℹ️ **Notice:** The selected model encountered an error. Automatically switching to **✨ Gemini 3.6 Flash** to complete your request...\n\n---\n\n"
                }
                yield from self._execute_gemini(
                    prompt=prompt,
                    ghl=ghl,
                    is_ghl_connected=is_ghl_connected,
                    system_instruction=system_instruction,
                    model_name="gemini-3.6-flash",
                    location_id=location_id,
                    access_token=access_token,
                    history=history,
                    intent=intent,
                    attachments=attachments
                )
                return
            yield {"type": "chunk", "text": f"⚠️ **{provider_name} Execution Error:** {str(e)}"}

    def _dispatch_tool_call(self, ghl: GHLSubAccountClient, tool_name: str, tool_args: Dict[str, Any], location_id: str, access_token: str) -> Dict[str, Any]:
        """Dispatches an abstract tool name to the concrete GHL REST client."""
        if not location_id or not access_token:
            return {
                "success": False,
                "error": "Location ID & Access Token missing. Please click 'Connect Sub-Account' at the top bar to connect your GHL Sub-Account."
            }

        try:
            if tool_name == "create_contact":
                return ghl.create_contact(**tool_args)
            elif tool_name == "search_contacts":
                return ghl.search_contacts(**tool_args)
            elif tool_name == "create_pipeline":
                return ghl.create_pipeline(**tool_args)
            elif tool_name == "get_pipelines":
                return ghl.get_pipelines()
            elif tool_name == "create_opportunity":
                return ghl.create_opportunity(**tool_args)
            elif tool_name == "create_tag":
                return ghl.create_tag(**tool_args)
            elif tool_name == "create_custom_field":
                return ghl.create_custom_field(**tool_args)
            elif tool_name == "send_conversation_message":
                return ghl.send_conversation_message(**tool_args)
            elif tool_name == "create_contact_task":
                return ghl.create_contact_task(**tool_args)
            elif tool_name == "create_contact_note":
                return ghl.create_contact_note(**tool_args)
            elif tool_name == "setup_gym_subaccount":
                return ghl.setup_gym_subaccount()
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}



