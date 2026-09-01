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


def get_token_budget(provider: str, intent: str) -> int:
    """
    Returns the optimal max_tokens for a given provider × intent combination.
    Guarantees sufficient token space so full HTML/CSS code blocks and tables are NEVER truncated.
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
    return budgets.get(provider, budgets['groq']).get(intent, 4000)


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

    # If building a fresh architecture (full_build), start with 100% clean context to eliminate context pollution & token waste
    if intent == "full_build":
        return []

    if max_messages <= 0:
        max_messages = 6 if provider == 'gemini' else 4

    trimmed = list(history[-max_messages:])
    max_assistant_chars = 1000 if provider == 'groq' else 1800

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
    Detects if a response was likely truncated mid-generation.
    Checks for unclosed HTML applications, unclosed code fences, mid-tag cutoffs, etc.
    """
    if not text or len(text) < 100:
        return False

    # Check if an HTML application was started but not closed
    if "<!DOCTYPE html" in text or "<html" in text:
        if "</html>" not in text:
            return True

    # Check for unclosed markdown code fences
    fence_count = text.count('```')
    if fence_count % 2 != 0:
        return True

    clean_end = text.strip()
    if clean_end.endswith(('<', '=', '"', "'", '(', '{', '[', ':', ',')):
        return True

    # Check if text ends mid-sentence (no terminal punctuation in last 80 chars)
    last_segment = clean_end[-80:]
    if last_segment and not any(last_segment.endswith(c) for c in ('.', '!', '?', '|', ']', '`', '>', '*')):
        return True

    return False

# AI Models Catalog categorized by Provider
MODELS_CATALOG = [
    # Google Gemini Models (Active Key Pool)
    {
        "id": "gemini-3.6-flash",
        "name": "Gemini 3.6 Flash (Recommended)",
        "provider": "gemini",
        "category": "Google Gemini",
        "badge": "✨ Multimodal & Tools",
        "supports_tools": True,
        "description": "Latest state-of-the-art multimodal Gemini model with native GHL function calling and high speed."
    },
    {
        "id": "gemini-3.7-flash",
        "name": "Gemini 3.7 Flash",
        "provider": "gemini",
        "category": "Google Gemini",
        "badge": "Advanced Reasoning",
        "supports_tools": True,
        "description": "Hybrid reasoning model for high precision CRM workflows and complex multi-step automations."
    },
    {
        "id": "gemini-3.5-flash",
        "name": "Gemini 3.5 Flash",
        "provider": "gemini",
        "category": "Google Gemini",
        "badge": "High Speed",
        "supports_tools": True,
        "description": "Optimized for quick turnaround CRM tasks and automated workflows."
    },
    {
        "id": "gemini-flash-latest",
        "name": "Gemini Flash Latest",
        "provider": "gemini",
        "category": "Google Gemini",
        "badge": "High Speed",
        "supports_tools": True,
        "description": "Latest general-purpose Gemini Flash model."
    },

    # Groq Cloud Ultra-Fast Models
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
        "id": "groq/compound",
        "name": "Groq Compound Flagship",
        "provider": "groq",
        "category": "Groq Ultra-Fast",
        "badge": "🧠 Flagship Reasoning",
        "supports_tools": True,
        "description": "Full-capacity Groq Compound architecture for deep architectural logic."
    },
    {
        "id": "qwen/qwen3.8-27b",
        "name": "Groq Qwen 3.8 27B",
        "provider": "groq",
        "category": "Groq Ultra-Fast",
        "badge": "High Speed",
        "supports_tools": True,
        "description": "Lightning-fast execution on Groq LPU with full GHL function calling."
    },
    {
        "id": "qwen/qwen3.6-27b",
        "name": "Groq Qwen 3.6 27B",
        "provider": "groq",
        "category": "Groq Ultra-Fast",
        "badge": "Low Latency",
        "supports_tools": True,
        "description": "High-throughput model tuned for real-time CRM chat."
    },
    {
        "id": "openai/gpt-oss-120b",
        "name": "Groq GPT-OSS 120B",
        "provider": "groq",
        "category": "Groq Ultra-Fast",
        "badge": "High Capacity",
        "supports_tools": True,
        "description": "Large-scale reasoning model hosted on Groq LPU."
    },
    {
        "id": "openai/gpt-oss-20b",
        "name": "Groq GPT-OSS 20B",
        "provider": "groq",
        "category": "Groq Ultra-Fast",
        "badge": "Fast Inference",
        "supports_tools": True,
        "description": "Compact foundation model hosted on Groq."
    },
    {
        "id": "allam-2-7b",
        "name": "Groq Allam 2 7B",
        "provider": "groq",
        "category": "Groq Ultra-Fast",
        "badge": "Bilingual",
        "supports_tools": False,
        "description": "Fast conversational engine with Arabic & English multilingual support."
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
        "description": "Create a Custom Field (TEXT, NUMBER, DATE, etc.) in the sub-account.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING", "description": "Name of custom field"},
                "data_type": {"type": "STRING", "description": "Data type: TEXT, NUMBER, DATE, SINGLE_OPTIONS"}
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
    High-Performance AI Action Execution Engine for GoHighLevel supporting Google Gemini and Groq Cloud LPU.
    """
    def __init__(self, gemini_key: str = "", groq_key: str = "", openrouter_key: str = ""):
        self.gemini_key = gemini_key.strip()
        self.groq_key = groq_key.strip()
        self.openrouter_key = openrouter_key.strip()
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
        Processes prompt via Gemini or Groq Cloud API, determines tool calls, executes GHL API commands, and yields SSE stream updates.
        Supports multimodal attachments (images, PDFs, documents, code).
        """
        provider = detect_provider(model_name)
        ghl = GHLSubAccountClient(location_id=location_id, access_token=access_token)
        
        # Check connection status first if credentials provided
        if location_id and access_token:
            conn_status = ghl.verify_connection()
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
=============================================================================
MANDATORY GOHIGHLEVEL (GHL) OPERATIONAL & ARCHITECTURAL RULES
=============================================================================
""" + """
1. KEEP CORRECT INFORMATION:
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

        # Direct Q&A, Job Proposals, Consultations, or General Requests
        if intent == "quick_answer":
            return base_prompt + f"""
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
TASK DIRECTIVE: ITERATIVE MODIFICATION & REFINEMENT
=============================================================================
- The user is modifying or refining a previously discussed configuration or asset.
- Focus on the requested modifications with senior-architect precision while keeping full code blocks complete.
- DO NOT output bracketed tags like `[RECOMMENDED]`, `[VERIFIED]`.
{tool_block}
"""

        # For full_build or custom builds
        return base_prompt + f"""
=============================================================================
TASK DIRECTIVE: COMPLETE PRODUCTION ARCHITECTURE & FULL CODE BUILD
=============================================================================
- Output the complete, enterprise-grade architecture with executive formatting.
- Deliver Section 1 FIRST so the complete interactive code artifact is 100% built and rendered immediately:
  1. 🚀 Complete Single-File Interactive HTML/CSS/JS Funnel Application (````html <!DOCTYPE html> ... </html> ````)
     • Use Tailwind CSS CDN (`<script src="https://cdn.tailwindcss.com"></script>`) with utility classes directly on HTML elements.
     • NEVER write custom `<style>` blocks or separate CSS rules (this wastes tokens).
     • Deliver ALL 5 STEPS (1. Opt-in, 2. VSL with 80% unlock, 3. 2-Step Checkout, 4. Upsell OTO, 5. Thank You) and complete interactive JavaScript navigation in the single block.
     • Guarantee the code completes 100% from `<!DOCTYPE html>` down to `</html>``` ` without stopping midway.
  2. 🗺️ Funnel Step Map & URLs (Compact Markdown Table)
  3. 📊 HighLevel Pipeline Stages, Custom Fields & Tags (Compact Markdown Tables)
  4. ⚡ Connected Drop-off Recovery Workflows (Crisp Action Blocks)
- DO NOT output bracketed tags like `[RECOMMENDED]`, `[VERIFIED]`.
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

                    # Auto-continuation for Gemini if output was truncated mid-sentence/code-fence
                    if stream_started and detect_truncation(accumulated_text):
                        logger.info(f"Gemini output truncated. Auto-triggering seamless continuation...")
                        try:
                            recent_tail = accumulated_text[-1800:]
                            last_cutoff = accumulated_text[-60:].replace('\n', ' ')
                            cont_contents = [
                                types.Content(role="user", parts=[types.Part.from_text(text=prompt)]),
                                types.Content(role="model", parts=[types.Part.from_text(text=f"...{recent_tail}")]),
                                types.Content(role="user", parts=[types.Part.from_text(text=f"Your response was cut off at: '{last_cutoff}'. Continue generating the remaining code and text EXACTLY from that point without repeating anything. Complete all remaining steps and close all tags cleanly.")])
                            ]
                            cont_stream = current_client.models.generate_content_stream(
                                model=mod,
                                contents=cont_contents,
                                config=types.GenerateContentConfig(**config_args)
                            )
                            for c_chunk in cont_stream:
                                if c_chunk.text:
                                    accumulated_text += c_chunk.text
                                    yield {"type": "chunk", "text": c_chunk.text}
                        except Exception as e_cont:
                            logger.warning(f"Gemini auto-continuation failed: {e_cont}")

                    if accumulated_text.count('```') % 2 != 0:
                        yield {"type": "chunk", "text": "\n```\n"}

                    gemini_key_pool.record_success(active_gemini_key)
                    return
                except Exception as e_mod:
                    if stream_started:
                        return
                    last_err_text = str(e_mod)
                    logger.warning(f"Gemini streaming with {mod} on key {active_gemini_key[:8]} failed: {e_mod}")
                    if "429" in last_err_text or "RESOURCE_EXHAUSTED" in last_err_text or "quota" in last_err_text.lower():
                        gemini_key_pool.mark_key_depleted(active_gemini_key, 429, last_err_text)
                        next_gemini_key = gemini_key_pool.get_active_key()
                        if next_gemini_key and next_gemini_key != active_gemini_key:
                            logger.info(f"Shifting Gemini key pool to next key: {next_gemini_key[:8]}...")
                            active_gemini_key = next_gemini_key
                            current_client = genai.Client(api_key=active_gemini_key)
                            continue
                        break
                    if "pro" in mod.lower() or "3.7" in mod.lower():
                        continue

            # Failover logic: Try OpenRouter Key Pool first, then Groq Cloud if Gemini is rate-limited / exhausted
            if not is_fallback:
                has_images = any(a.get("type") == "image" or str(a.get("mime_type", "")).startswith("image/") for a in (attachments or []))
                if self.openrouter_key:
                    from key_pool_manager import openrouter_key_pool
                    pool_key = openrouter_key_pool.get_active_key()
                    if pool_key:
                        logger.info("Gemini limit reached. Seamlessly failing over to OpenRouter (Llama 3.3 70B)...")
                        yield {
                            "type": "chunk",
                            "text": "> ℹ️ **Notice:** Google Gemini quota is currently full/rate-limited. Seamlessly routing your request to **OpenRouter (Llama 3.3 70B / Multi-Key Pool)**...\n\n---\n\n"
                        }
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
                            is_fallback=True,
                            attachments=attachments
                        )
                        return
                elif self.groq_key:
                    groq_target = "qwen/qwen3.8-27b"
                    logger.info("Falling back from Gemini stream to Groq Cloud...")
                    yield {
                        "type": "chunk",
                        "text": "> ℹ️ **Notice:** Google Gemini is currently rate-limited. Seamlessly switching to high-capacity **Groq Cloud** to complete your request...\n\n---\n\n"
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
        attachments: Optional[List[Dict[str, Any]]] = None
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
                "CRITICAL CODE ARTIFACT MANDATE:\n"
                "You MUST output the complete, 100% production-ready ```html <!DOCTYPE html> ... </html>``` code block "
                "containing ALL 5 steps (Opt-in, VSL, Checkout, Upsell, Thank You) and interactive JavaScript navigation. "
                "Use Tailwind CDN utilities (<script src=\"https://cdn.tailwindcss.com\"></script>) directly on elements. "
                "NEVER omit, truncate, or summarize the HTML code block."
            )

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
        target_max_tokens = get_token_budget("groq", intent)
        target_temp = get_temperature(intent, is_tool_mode=is_ghl_connected)

        # Validate Groq model name
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
                # Try with 800 max_tokens if 402 was due to upfront token credit limit
                if resp.status_code == 402 and payload.get("max_tokens", 1000) > 800:
                    logger.info("OpenRouter 402 credit cap hit. Retrying with reduced max_tokens=800...")
                    payload["max_tokens"] = 800
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
                max_continuations = 2
                while (finish_reason == "length" or detect_truncation(accumulated_text)) and max_continuations > 0:
                    max_continuations -= 1
                    logger.info(f"Auto-continuation triggered for {provider_name} (finish_reason={finish_reason}, len={len(accumulated_text)})")
                    recent_tail = accumulated_text[-1800:]
                    last_cutoff = accumulated_text[-60:].replace('\n', ' ')
                    cont_messages = [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": f"...{recent_tail}"},
                        {
                            "role": "user",
                            "content": f"Your response was cut off at: '{last_cutoff}'. Continue generating the remaining code and text EXACTLY from that point without repeating previous text. Complete all remaining sections and close all tags cleanly."
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
                                                accumulated_text += c_text
                                                yield {"type": "chunk", "text": c_text}
                                        except Exception:
                                            pass
                        else:
                            break
                    except Exception as e_cont:
                        logger.warning(f"Continuation request failed: {e_cont}")
                        break

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
                    history=history
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
                    history=history
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
