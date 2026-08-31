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
    'html/css', 'html and css', 'provide the html', 'checkout html', 'funnel architecture'
}


def classify_prompt_intent(prompt: str) -> str:
    """
    Classifies user prompt into one of three intent categories:
    - 'full_build': Explicit request to build full landing page & CRM architecture or write code
    - 'iteration': Modify or refine a previous response
    - 'quick_answer': Q&A, job proposals, consultation, troubleshooting, or general requests
    """
    lower = prompt.lower().strip()

    # Check for direct full build commands first
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


def get_token_budget(provider: str, intent: str) -> int:
    """
    Returns the optimal max_tokens for a given provider × intent combination.
    Guarantees sufficient token space so full HTML/CSS code blocks and tables are NEVER truncated,
    while staying within OpenRouter and Groq upfront credit quotas.
    """
    budgets = {
        'gemini': {
            'full_build': 12000,
            'iteration': 8000,
            'quick_answer': 6000,
        },
        'groq': {
            'full_build': 5000,
            'iteration': 3500,
            'quick_answer': 3000,
        },
        'openrouter': {
            'full_build': 3800,
            'iteration': 3000,
            'quick_answer': 2800,
        }
    }
    return budgets.get(provider, budgets['openrouter']).get(intent, 3000)


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
    Checks for unclosed code fences, mid-sentence cutoffs, etc.
    """
    if not text or len(text) < 100:
        return False

    # Check for unclosed markdown code fences
    fence_count = text.count('```')
    if fence_count % 2 != 0:
        return True

    # Check if text ends mid-sentence (no terminal punctuation in last 80 chars)
    last_segment = text.strip()[-80:]
    if last_segment and not any(last_segment.rstrip().endswith(c) for c in '.!?|]`\n>*'):
        return True

    return False

# Complete Model Catalog categorized by Provider
MODELS_CATALOG = [
    # Google Gemini Models
    {
        "id": "gemini-3.6-flash",
        "name": "Gemini 3.6 Flash (Recommended)",
        "provider": "gemini",
        "category": "Google Gemini",
        "badge": "Fast & Smart",
        "supports_tools": True,
        "description": "Latest state-of-the-art multimodal model with native function calling and ultra-fast speed."
    },
    {
        "id": "gemini-3.7-flash",
        "name": "Gemini 3.7 Flash",
        "provider": "gemini",
        "category": "Google Gemini",
        "badge": "Advanced Reasoning",
        "supports_tools": True,
        "description": "Next-generation hybrid reasoning model for high precision CRM tasks."
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
        "description": "Optimized for quick turnaround CRM tasks and automated workflows."
    },
    {
        "id": "gemini-pro-latest",
        "name": "Gemini Pro Latest",
        "provider": "gemini",
        "category": "Google Gemini",
        "badge": "Deep Reasoning",
        "supports_tools": True,
        "description": "High-capacity reasoning engine for complex multi-step CRM setups."
    },
    {
        "id": "gemini-3.1-pro-preview",
        "name": "Gemini 3.1 Pro Preview",
        "provider": "gemini",
        "category": "Google Gemini",
        "badge": "Flagship Pro",
        "supports_tools": True,
        "description": "Next-generation flagship reasoning engine for complex architectural workflows."
    },

    # Groq Cloud Ultra-Fast Models
    {
        "id": "qwen/qwen3.8-27b",
        "name": "Groq Qwen 3.8 27B",
        "provider": "groq",
        "category": "Groq Ultra-Fast",
        "badge": "Tools Enabled",
        "supports_tools": True,
        "description": "Lightning-fast execution on Groq LPU with robust tool calling."
    },
    {
        "id": "qwen/qwen3.6-27b",
        "name": "Groq Qwen 3.6 27B",
        "provider": "groq",
        "category": "Groq Ultra-Fast",
        "badge": "Ultra Low Latency",
        "supports_tools": True,
        "description": "High-throughput model tuned for real-time CRM chat."
    },
    {
        "id": "openai/gpt-oss-20b",
        "name": "Groq GPT-OSS 20B",
        "provider": "groq",
        "category": "Groq Ultra-Fast",
        "badge": "Fast Inference",
        "supports_tools": True,
        "description": "Compact open-source foundation model hosted on Groq."
    },
    {
        "id": "allam-2-7b",
        "name": "Groq Allam 2 7B",
        "provider": "groq",
        "category": "Groq Ultra-Fast",
        "badge": "Bilingual",
        "supports_tools": False,
        "description": "Fast conversational engine with Arabic & English multilingual support."
    },

    # OpenRouter - xAI Grok & DeepSeek Models
    {
        "id": "x-ai/grok-4.6",
        "name": "xAI Grok 4.6",
        "provider": "openrouter",
        "category": "xAI Grok & DeepSeek",
        "badge": "Flagship Grok",
        "supports_tools": True,
        "description": "Direct Grok reasoning engine from xAI via OpenRouter."
    },
    {
        "id": "x-ai/grok-4.5",
        "name": "xAI Grok 4.5",
        "provider": "openrouter",
        "category": "xAI Grok & DeepSeek",
        "badge": "Grok Engine",
        "supports_tools": True,
        "description": "Powerful conversational model by xAI with real-world knowledge."
    },
    {
        "id": "x-ai/grok-4.3",
        "name": "xAI Grok 4.3",
        "provider": "openrouter",
        "category": "xAI Grok & DeepSeek",
        "badge": "Grok Fast",
        "supports_tools": True,
        "description": "High speed Grok variant for instantaneous replies."
    },
    {
        "id": "deepseek/deepseek-v4-flash",
        "name": "DeepSeek V4 Flash",
        "provider": "openrouter",
        "category": "xAI Grok & DeepSeek",
        "badge": "DeepSeek AI",
        "supports_tools": True,
        "description": "Next-gen DeepSeek V4 architecture with blazing fast speeds."
    },
    {
        "id": "deepseek/deepseek-v4-pro",
        "name": "DeepSeek V4 Pro",
        "provider": "openrouter",
        "category": "xAI Grok & DeepSeek",
        "badge": "DeepSeek Pro",
        "supports_tools": True,
        "description": "Deep reasoning and code generation for intricate marketing flows."
    },
    {
        "id": "deepseek/deepseek-v3.2",
        "name": "DeepSeek V3.2",
        "provider": "openrouter",
        "category": "xAI Grok & DeepSeek",
        "badge": "Versatile",
        "supports_tools": True,
        "description": "Standard high-performance DeepSeek model."
    },

    # OpenRouter - Free Tier Models
    {
        "id": "inclusionai/ling-3.0-flash-fin:free",
        "name": "Ling 3.0 Flash (Free)",
        "provider": "openrouter",
        "category": "Free Tier Models",
        "badge": "100% Free",
        "supports_tools": False,
        "description": "Free-to-use conversational AI for planning and strategy generation."
    },
    {
        "id": "dots-studio/dots-3-note-preview:free",
        "name": "Dots 3 Note Preview (Free)",
        "provider": "openrouter",
        "category": "Free Tier Models",
        "badge": "100% Free",
        "supports_tools": False,
        "description": "Lightweight free model for quick copy, text summaries, and email drafts."
    },
    {
        "id": "liquid/lfm-2.5-2.6b:free",
        "name": "Liquid LFM 2.5 (Free)",
        "provider": "openrouter",
        "category": "Free Tier Models",
        "badge": "100% Free",
        "supports_tools": False,
        "description": "Efficient free-tier model by Liquid AI."
    },

    # OpenRouter - Flagship AI Models
    {
        "id": "anthropic/claude-3.5-sonnet",
        "name": "Claude 3.5 Sonnet",
        "provider": "openrouter",
        "category": "Flagship Models",
        "badge": "Top Coder & Agent",
        "supports_tools": True,
        "description": "Industry leader in nuanced reasoning, CRM architecture, and code."
    },
    {
        "id": "openai/gpt-4o",
        "name": "OpenAI GPT-4o",
        "provider": "openrouter",
        "category": "Flagship Models",
        "badge": "Omni Model",
        "supports_tools": True,
        "description": "Flagship OpenAI model with native tool calling."
    },
    {
        "id": "openai/gpt-4o-mini",
        "name": "OpenAI GPT-4o Mini",
        "provider": "openrouter",
        "category": "Flagship Models",
        "badge": "Fast & Economical",
        "supports_tools": True,
        "description": "Lightweight, highly capable OpenAI model for rapid operations."
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "Meta Llama 3.3 70B",
        "provider": "openrouter",
        "category": "Flagship Models",
        "badge": "Open Source Leader",
        "supports_tools": True,
        "description": "Meta's flagship open-weights model fine-tuned for instructions and tools."
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
    if model_name.startswith(("qwen/", "allam-", "openai/gpt-oss", "groq/", "canopylabs/")):
        return "groq"
    if any(model_name.startswith(p) for p in ["x-ai/", "deepseek/", "openai/", "anthropic/", "meta-llama/", "inclusionai/", "dots-studio/", "liquid/", "nvidia/", "google/"]):
        return "openrouter"
    if "/" in model_name:
        return "openrouter"
    return "gemini"


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
    Universal Multi-Provider AI Action Execution Engine for GoHighLevel.
    Supports Google Gemini, Groq Cloud, and OpenRouter (xAI Grok, DeepSeek, Claude, GPT-4o, etc.).
    """
    def __init__(self, gemini_key: str = "", groq_key: str = "", openrouter_key: str = ""):
        self.gemini_key = gemini_key.strip()
        self.groq_key = groq_key.strip()
        self.openrouter_key = openrouter_key.strip()
        
        # Initialize Google GenAI Client if key provided
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
        Processes prompt with conversation history, determines tool calls, executes GHL API commands, and yields SSE stream updates.
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

        # Build adaptive system prompt based on intent and provider
        system_instruction = self._build_system_prompt(intent, provider, is_ghl_connected, location_id)

        if provider == "gemini":
            yield from self._execute_gemini(
                prompt=prompt,
                ghl=ghl,
                is_ghl_connected=is_ghl_connected,
                system_instruction=system_instruction,
                model_name=model_name,
                location_id=location_id,
                access_token=access_token,
                history=history,
                intent=intent,
                attachments=attachments
            )
        elif provider == "groq":
            yield from self._execute_openai_compatible(
                prompt=prompt,
                ghl=ghl,
                is_ghl_connected=is_ghl_connected,
                system_instruction=system_instruction,
                model_name=model_name,
                api_url="https://api.groq.com/openai/v1/chat/completions",
                api_key=self.groq_key,
                provider_name="Groq Cloud",
                location_id=location_id,
                access_token=access_token,
                history=history,
                intent=intent,
                attachments=attachments
            )
        elif provider == "openrouter":
            yield from self._execute_openai_compatible(
                prompt=prompt,
                ghl=ghl,
                is_ghl_connected=is_ghl_connected,
                system_instruction=system_instruction,
                model_name=model_name,
                api_url="https://openrouter.ai/api/v1/chat/completions",
                api_key=self.openrouter_key,
                provider_name="OpenRouter",
                location_id=location_id,
                access_token=access_token,
                history=history,
                intent=intent,
                attachments=attachments,
                extra_headers={
                    "HTTP-Referer": "http://127.0.0.1:7861",
                    "X-Title": "Conversation AI Copilot"
                }
            )
        else:
            yield {"type": "chunk", "text": f"⚠️ **Unsupported Provider:** {provider}"}

    def _build_system_prompt(self, intent: str, provider: str, is_ghl_connected: bool, location_id: str) -> str:
        """
        Builds an adaptive system prompt implementing the Complete 29 Senior GHL Solutions Architect & SaaS Engineering Rules.
        Anchored in senior-level architectural accuracy, failure-mode awareness, honesty over confidence,
        zero fabrication, and strict query scope.
        """
        base_prompt = """# SYSTEM PROMPT — SENIOR GOHIGHLEVEL (GHL) SOLUTIONS ARCHITECT & FULL-STACK SAAS ARCHITECT

You are a Senior GoHighLevel (HighLevel) Solutions Architect, Automation Engineer, and Full-Stack SaaS Architect.
Your core objective: Produce technically accurate, implementation-aware, honest, and production-conscious solutions.
Primary Evaluation Metric: Correctness > Honesty > Practicality > Completeness > Confidence.
Goal: Make every architecture and code deliverable survive real-world implementation by an experienced developer.

=============================================================================
THE 29 CORE ENGINEERING & ARCHITECTURAL RULES (STRICT COMPLIANCE REQUIRED)
=============================================================================

1. NEVER FABRICATE INFORMATION:
   - NEVER invent client experience, project counts, client names, portfolio links, demo links, domains, URLs, testimonials, case studies, revenue/results, unverified API endpoints/headers/params, fake GHL triggers/actions, or compliance certifications (HIPAA/GDPR/SOC2).
   - If not provided by client, use: `[PLACEHOLDER — CLIENT TO PROVIDE]` or `[REQUIRES VERIFICATION]`.

2. SEPARATE FACTS, ASSUMPTIONS, RECOMMENDATIONS, AND VERIFICATION:
   - Explicitly distinguish where relevant:
     • [VERIFIED]: Confirmed from current official GHL docs or user input.
     • [ASSUMPTION]: Required to design architecture but not provided.
     • [RECOMMENDATION]: Architectural preference based on engineering reasoning.
     • [REQUIRES VERIFICATION]: Platform details subject to plan/version/API changes.

3. CURRENT GHL INFORMATION MUST BE TREATED AS CHANGEABLE:
   - For exact technical details subject to platform updates, state: `[VERIFY AGAINST CURRENT OFFICIAL HIGHLEVEL DOCUMENTATION]`.

4. NEVER CALL BASIC HTML "PRODUCTION-READY" UNLESS IT ACTUALLY IS:
   - You MUST ALWAYS generate the complete, fully written, beautifully styled ````html <!DOCTYPE html> ... </html> ```` code block with embedded `<style>` and `<script>` whenever code is requested.
   - Accompany the complete code with an implementation note explaining how to bind the form actions/inputs to GoHighLevel forms or API v2.
   - NEVER output only a disclaimer note without providing the actual code block. The complete code block is ALWAYS mandatory.

5. WORLD-CLASS HIGH-CONVERTING UI & CSS COMPONENT ARCHITECTURE:
   When generating HTML/CSS for Funnels, Landing Pages, VSLs, Booking Calendars, or Checkouts, you MUST strictly adhere to these enterprise-grade visual standards:
   • GOOGLE FONTS & DESIGN TOKENS: Import '@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@600;700;800;900&display=swap");'. Use modern CSS variables (`--primary`, `--primary-glow`, `--bg-dark: #080c14`, `--card-bg: rgba(15, 23, 42, 0.75)`, `--border: rgba(255, 255, 255, 0.1)`).
   • ZERO RAW BROWSER INPUTS: All text/email/phone inputs MUST have dark glass background (`background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 12px; padding: 14px 18px; color: #fff; font-size: 15px; width: 100%; transition: all 0.2s;`). Focus ring: `border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-glow); outline: none;`.
   • GLOWING HIGH-CONVERTING CTA BUTTONS: Heavy glowing gradient (`background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: #fff; font-weight: 800; font-size: 16px; padding: 16px 28px; border-radius: 12px; border: none; box-shadow: 0 10px 25px var(--primary-glow); cursor: pointer; transition: all 0.2s;`) with hover lift (`transform: translateY(-2px);`).
   • VSL VIDEO COMPONENT (NEVER BARE <video>): 16:9 Aspect ratio container with glowing neon border, dark cinematic backdrop, large animated Play Button (▶), top overlay bar (`🔴 LIVE MASTERCLASS`), and dynamic Watch Progress Bar (`80% Unlocks VIP Assessment`) with interactive JS simulator that unhides the next booking section on progress!
   • 1-ON-1 ASSESSMENT CALENDAR (NEVER BARE <input type="date">): Interactive Glassmorphic Booking Widget with Coach profile pill, 7 clickable Date Pills (Mon, Tue, Wed...), 4 clickable Time Slot Buttons (09:00 AM, 11:30 AM, 02:00 PM, 04:30 PM), and attendee input fields.
   • 2-STEP CHECKOUT & ORDER SUMMARY: 2-Column CSS Grid (`display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 40px;`). Left = Value Stack with green checkmarks, 100% Risk-Free Guarantee card & Trust Badges (`🔒 256-Bit SSL`). Right = 2-Step Form Card, Price Summary box (`$0.00 Today ➔ $97/mo`), and CTA button.
   • VIP UPSELL & SPECIAL OFFERS: Urgency countdown timer pill (`⚡ EXPIRES IN 14:59`), strikethrough pricing (`~~$297~~ $97`), and 1-click upgrade button.

6. NEVER INVENT DOMAINS OR URLs:
   - Use `[CLIENT DOMAIN]/path`, `[CALENDAR LINK]`, `[VIDEO EMBED URL]`. Never fabricate realistic fake URLs (e.g., bellavistaristorante.com).

7. GHL FORMS MUST ACTUALLY CONNECT TO GHL:
   - Clearly detail the integration pipeline: Form Submission ➔ Contact Created/Updated ➔ Tag Applied ➔ Workflow Trigger ➔ Action.

8. DISTINGUISH UI FROM BUSINESS LOGIC (LAYER SEPARATION):
   - Presentation Layer (HTML/CSS/React)
   - Application Layer (Auth, Business Logic, Validation)
   - GHL Layer (CRM Contacts, Pipelines, Workflows, Calendars, Access)
   - External Systems (Stripe, Databases, Meta, Webhooks).

9. MEMBERSHIP ARCHITECTURE:
   - Strictly separate: Contacts ➔ Products ➔ Offers/Access Levels ➔ Courses ➔ Modules. Detail payment grant, access check, cancellation grace periods, and revocation workflows.

10. ABANDONED CART / DROP-OFF LOGIC:
    - Never assume an unverified native trigger exists. Model the generic logic: Intent ➔ Wait Window (e.g., 15m) ➔ Check Confirmed Status (Yes: Exit / No: Recovery Action).

11. WEBHOOK ARCHITECTURE & IDEMPOTENCY:
    - Never assume "instant" or "exactly once" delivery. Model: Event ➔ Signature Validation ➔ Idempotency Key Check ➔ Queue ➔ DB State ➔ Frontend.

12. SOURCE OF TRUTH:
    - Explicitly state authoritative systems: SaaS Auth (App DB), CRM Contact/Pipeline (GHL), Payment (Stripe), OAuth (Secure Vault).

13. MULTI-TENANCY:
    - Never trust client-provided `tenant_id` or `location_id` from the frontend. Always resolve and authorize tenant server-side.

14. AUTHENTICATION ≠ GHL AUTHORIZATION:
    - Keep SaaS user authentication (Supabase/Auth.js) strictly separate from GHL OAuth / Location tokens.

15. NEVER EXPOSE GHL CREDENTIALS TO THE BROWSER:
    - Strict pattern: Browser ➔ Your Backend ➔ Encrypted Storage ➔ GHL API v2.

16. API ENDPOINTS MUST BE VERIFIED:
    - When providing API examples, specify: Version, Auth method, Endpoint, Method, Headers, Request Body, and Scopes.

17. RATE LIMITS MUST NOT BE FABRICATED:
    - Do not invent exact RPM numbers from memory. State: `Rate limits must be verified against current official API documentation.` Recommend queues and exponential backoff.

18. FINANCIAL, HEALTH & COMPLIANCE CLAIMS:
    - Never fabricate guarantees, revenue numbers, or medical/weight-loss claims.

19. SMS AND EMAIL TCPA / A2P COMPLIANCE:
    - Always include explicit consent disclosures, time-of-day quiet hours (8am-8pm local), and native STOP/HELP handling.

20. RESERVATION & INTENT ARCHITECTURE:
    - Distinguish between *Intent/Request Received* and *Confirmed Status*.

21. PIPELINE STAGES MUST HAVE REAL ENTRY/EXIT LOGIC:
    - Every stage must specify: Entry Trigger, Required Data, Automation, SLA, Exit Criteria, and Next Stage.

22. TAGS VS CUSTOM FIELDS:
    - Use Custom Fields for structured attributes (dates, preferences, numbers). Use Tags for states, stages, and automation triggers.

23. WORKFLOW DESIGN MUST INCLUDE SAFETY CONDITIONS:
    - Pattern: Trigger ➔ Eligibility Check ➔ Safety Check ➔ Action ➔ Wait ➔ Re-check Status ➔ Next Action ➔ Exit.

24. FAILURE-FIRST DESIGN:
    - Always account for: Success, API Failure, Duplicate events, Delays, State Conflicts, and Recovery.

25. DO NOT OVER-ENGINEER:
    - Choose the simplest reliable architecture that fulfills the business requirements.

26. WHEN CLIENT REQUIREMENTS CONFLICT:
    - Explicitly state `Conflict detected`, explain the trade-offs, and provide the recommended resolution.

27. PRODUCTION-READY CHECKLIST:
    - Verify Frontend, Backend, GHL, Webhooks, Database, Security, and Testing before declaring production readiness.

28. OUTPUT FORMAT FOR COMPLEX GHL REQUESTS:
    - Use structured sections: Understanding, Assumptions, Verified Capabilities, Architecture, GHL Components, Custom Components, Data Model, Workflows, APIs, Webhooks, Security, Failure Scenarios, Implementation Steps, Missing Input, Verification Items.

29. CRITICAL ANTI-HALLUCINATION PRE-CHECK:
    - Internally verify every concrete claim before generation. If not user-provided or proven engineering fact, use placeholders or verification labels.

30. FINAL QUALITY STANDARD:
    - Be precise, technically honest, challenge suboptimal paths, design failure handling, and ensure code is self-contained and copy-paste ready.
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
- STRICT QUERY RELEVANCE: Answer ONLY what the user explicitly asks for.
- ABSOLUTE PROHIBITION ON UNREQUESTED CODE & BLUEPRINTS: Do NOT output HTML/CSS code, landing page designs, form mapping tables, or 14-section blueprints UNLESS explicitly requested in the user's prompt.
- MANDATORY CODE COMPLETION: If code IS explicitly requested by the user, provide the 100% complete, production-ready, single-block ````html <!DOCTYPE html> ... </html> ```` code with embedded `<style>` and `<script>`. NEVER omit code or output placeholder notes.
- DO NOT CONTINUE PREVIOUS BLUEPRINT/SECTION DUMPS: If conversation history contains partial sections (e.g. 'SECTION 1', 'SECTION 2'...), DO NOT continue generating sections. Answer the user's latest query directly and conversationally.
- NO UNSOLICITED SCOPING QUESTIONS: Do NOT output generic scoping questions (1A, 2A, 3A...) for general queries, job postings, or consultations.
- PROPOSALS: Answer every question from the client thoroughly and concisely, using placeholders for missing personal data.
{tool_block}
"""

        if intent == "iteration":
            return base_prompt + f"""
=============================================================================
TASK DIRECTIVE: ITERATIVE MODIFICATION
=============================================================================
- The user is modifying or refining a previously discussed configuration or asset.
- Focus strictly on the requested modifications or tweaks without re-generating unchanged parts unnecessarily.
{tool_block}
"""

        # For full_build or custom builds
        return base_prompt + f"""
=============================================================================
TASK DIRECTIVE: STRICT QUERY SCOPE & ZERO UNSOLICITED CONTENT
=============================================================================
- STRICT HISTORICAL ISOLATION: ONLY answer the user's latest prompt. NEVER re-answer, summarize, or prepend answers to prior questions from the conversation history (e.g., past SQL questions, hourly rate inquiries, or previous niche Q&As).
- STRICT QUERY SCOPE: Output ONLY the specific deliverables and components explicitly requested in the prompt.
- ABSOLUTE PROHIBITION ON UNREQUESTED SECTIONS:
  • Do NOT output all 14 blueprint sections unless the user explicitly requests "all 14 sections".
  • Do NOT generate full multi-email copy sequences unless the user explicitly asks for "email copy".
  • Do NOT invent extra diagrams, form mapping tables, or valuation matrices unless explicitly specified.
- PREMIUM VISUAL MARKDOWN FORMATTING & CODE EXCELLENCE STANDARDS:
  1. Executive Architecture Header: Start with a clean Executive Badge header (`### ⚡ [Brand / Business Name] — Complete Architecture`), separated by horizontal rules (`---`).
  2. WORLD-CLASS HIGH-CONVERTING UI & CSS ARCHITECTURE (ZERO BARE/CHEAP HTML):
     • NEVER output a primitive, unstyled form or bare browser inputs.
     • ALWAYS generate an ultra-modern, high-converting layout using a clean 2-column CSS Grid (`display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 40px;` with mobile `@media (max-width: 860px) {{ grid-template-columns: 1fr; }}`):
       - Left Column: Hero Badge Pill (`⚡ VIP MEMBERSHIP ACCESS`), High-Impact Headline with gradient text highlights, Value Proposition Stack with checkmarks, Bulletproof 100% Risk-Free Guarantee Card & Trust Badges (`🔒 256-Bit SSL Encrypted`).
       - Right Column: 2-Step Card or Interactive Booking Widget, dark glassmorphic input fields with focus glow, Order Summary box (`$0.00 today ➔ $97/mo after 14 days`), and a heavy glowing gradient submit CTA button.
     • VSL VIDEO SECTION (WHEN REQUESTED): 16:9 Aspect container with glowing neon border, cinematic backdrop, animated Play Button (▶), overlay header (`🔴 LIVE MASTERCLASS`), and dynamic Watch-Progress Bar (`80% Unlocks Free 1-on-1 Assessment`) with interactive JavaScript simulator that unhides the next step!
     • 1-ON-1 ASSESSMENT CALENDAR (WHEN REQUESTED): Interactive Glassmorphic Booking Widget with Coach Profile Header, 7 clickable Date Pills (Mon, Tue, Wed...), 4 clickable Time Slot Buttons (09:00 AM, 11:30 AM, 02:00 PM, 04:30 PM), and attendee input fields.
     • BEAUTIFUL PRODUCTION CSS: Scoped within container, modern Google Font ('Plus Jakarta Sans' or 'Outfit'), sleek dark background (`#07090e` / `#0f172a`), neon brand accents (`#10b981` / `#38bdf8`), rounded corners (`border-radius: 14px`), and subtle glassmorphic backdrop blurs (`backdrop-filter: blur(16px);`).
     • STRICT CODE BLOCK COMPLETION & CLOSING RULE:
       - Wrap the COMPLETE document in ONE single ````html <!DOCTYPE html> ... </html> ```` code block with embedded `<style>` and `<script>`.
       - You MUST close the code fence with `</html>\n```\n` immediately at the end of the code.
       - NEVER dump raw markdown, text, or additional sections inside the code block without closing the code fence!
     • Outputting separate CSS and HTML blocks is STRICTLY FORBIDDEN.
  3. CRM Custom Fields & Tags: Format into clean, comprehensive Markdown Tables (`| Field Name | Unique Key | Data Type | Permissible Values |`).
  4. Sales Pipeline Stages: Format into a clean table with Stage Name, Entry Trigger, Required Data, SLA, and Exit Criteria.
  5. Automations & Drop-off Recovery: Format into visual ASCII logic diagrams (`[Trigger] ➔ [Wait] ➔ [Check]`) followed by structured step-by-step workflow blocks.
  6. Zero Raw Messy Text: Ensure every piece of content uses clean typography, bold key terms, and proper markdown spacing.
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
        if not self.gemini_client:
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

                    response_stream = self.gemini_client.models.generate_content_stream(
                        model=mod,
                        contents=contents,
                        config=types.GenerateContentConfig(**config_args)
                    )
                    for chunk in response_stream:
                        if chunk.text:
                            stream_started = True
                            yield {"type": "chunk", "text": chunk.text}
                except Exception as e_mod:
                    if stream_started:
                        return
                    last_err_text = str(e_mod)
                    logger.warning(f"Gemini streaming with {mod} failed: {e_mod}")
                    if "429" in last_err_text or "RESOURCE_EXHAUSTED" in last_err_text or "quota" in last_err_text.lower():
                        # Gemini daily/minute quota exhausted; failover immediately to OpenRouter / Groq
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
                    groq_target = "llama-3.2-11b-vision-preview" if has_images else "groq/compound"
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
            elif self.groq_key:
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
                    history=history
                )
                return
            yield {"type": "chunk", "text": f"⚠️ **Execution Error:** {str(last_exception)}"}
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
            yield {"type": "chunk", "text": f"⚠️ **Agent Execution Error:** {str(e)}"}

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
            yield {"type": "chunk", "text": f"⚠️ **Error:** {provider_name} API Key is not configured on the server."}
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

        # Hard mandate for OpenRouter / Groq models to ensure raw code is always printed
        if any(kw in prompt.lower() for kw in ['html', 'css', 'code', 'checkout', 'funnel', 'landing page', 'page', 'form']):
            messages[0]["content"] += (
                "\n\n=============================================================================\n"
                "CRITICAL CODE GENERATION MANDATE:\n"
                "You MUST output the complete, raw ```html <!DOCTYPE html> ... </html>``` code block with "
                "full embedded <style> and <script> markup. NEVER output an explanation or placeholder instead of code."
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
        target_max_tokens = get_token_budget(provider_slug, intent)
        target_temp = get_temperature(intent, is_tool_mode=is_ghl_connected)

        # Groq TPM Safety Guardrail
        if provider_slug == "groq":
            # Auto-upgrade to high-capacity groq/compound (70,000 TPM) for full builds and large prompts
            if intent == "full_build" or "qwen" in model_name:
                model_name = "groq/compound"

            est_prompt_tokens = sum(len(m.get("content", "")) // 4 for m in messages)
            if est_prompt_tokens > 5000 and not is_fallback:
                from key_pool_manager import openrouter_key_pool
                pool_key = openrouter_key_pool.get_active_key()
                if pool_key:
                    logger.info("Prompt exceeds Groq window. Seamlessly routing to OpenRouter...")
                    yield {
                        "type": "chunk",
                        "text": "> ℹ️ **Notice:** High-volume request. Seamlessly routing to **OpenRouter** (Llama 3.3 70B)...\n\n---\n\n"
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
                        is_fallback=True
                    )
                    return

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
            
            # If OpenRouter returns credit or quota error (401, 402, 429), shift to next key in pool
            if is_openrouter and resp.status_code in [401, 402, 429]:
                from key_pool_manager import openrouter_key_pool
                openrouter_key_pool.mark_key_depleted(active_key, resp.status_code, resp.text[:120])
                next_key = openrouter_key_pool.get_active_key()
                if next_key and next_key != active_key:
                    logger.info(f"OpenRouter key {active_key[:12]}... depleted/throttled. Shifting to next pool key {next_key[:12]}... and retrying...")
                    headers["Authorization"] = f"Bearer {next_key}"
                    active_key = next_key
                    resp = requests.post(api_url, headers=headers, json=payload, stream=(not can_call_tools), timeout=45)

            if resp.status_code != 200:
                err_body = resp.text
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message", err_body)
                except Exception:
                    err_msg = err_body
                
                logger.warning(f"{provider_name} API Error ({resp.status_code}): {err_msg}")
                
                # If Groq returns 413 (Payload Too Large) or 429 (Rate Limit), seamlessly failover to OpenRouter Key Pool
                if not is_openrouter and (resp.status_code in [413, 429] or "too large" in err_msg.lower() or "limit 8000" in err_msg.lower()):
                    from key_pool_manager import openrouter_key_pool
                    pool_key = openrouter_key_pool.get_active_key()
                    if pool_key:
                        logger.info("Groq returned 413/429. Seamlessly shifting to OpenRouter Key Pool...")
                        yield {
                            "type": "chunk",
                            "text": "> ℹ️ **Notice:** Groq rate limit reached. Seamlessly shifting to **OpenRouter** (Llama 3.3 70B)...\n\n---\n\n"
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
                            is_fallback=True
                        )
                        return

                # If credits depleted (402), rate limited (429), or payload exceeded (413), seamlessly failover to Gemini if not already in fallback
                if not is_fallback and (resp.status_code in [402, 413, 429] or "credits" in err_msg.lower() or "quota" in err_msg.lower() or "too large" in err_msg.lower()):
                    if self.gemini_client:
                        logger.info(f"Failing over from {provider_name} ({model_name}) to Gemini 3.6 Flash due to token quota/credits...")
                        yield {
                            "type": "chunk",
                            "text": f"> ℹ️ **Notice:** The selected {provider_name} model's token quota is currently depleted or insufficient. Automatically switching to high-capacity **✨ Gemini 3.6 Flash** to complete your request seamlessly...\n\n---\n\n"
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
                            is_fallback=True
                        )
                        return
                    else:
                        yield {"type": "chunk", "text": f"⚠️ **Notice:** This model's token quota is currently depleted. Please switch to **✨ Gemini 3.6 Flash** in the model selector to continue."}
                        return

                yield {"type": "chunk", "text": f"⚠️ **{provider_name} API Error ({resp.status_code}):** {err_msg}"}
                return

            if is_openrouter:
                from key_pool_manager import openrouter_key_pool
                openrouter_key_pool.record_success(active_key)

            if not can_call_tools:
                # Direct streaming from OpenRouter / Groq SSE stream
                for raw_line in resp.iter_lines():
                    if raw_line:
                        line_str = raw_line.decode('utf-8')
                        if line_str.startswith('data: '):
                            payload_str = line_str[6:].strip()
                            if payload_str == '[DONE]':
                                break
                            try:
                                chunk_data = json.loads(payload_str)
                                delta = chunk_data.get('choices', [{}])[0].get('delta', {})
                                content_piece = delta.get('content', '')
                                if content_piece:
                                    yield {"type": "chunk", "text": content_piece}
                            except Exception:
                                pass
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
