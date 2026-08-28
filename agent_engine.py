import os
import json
import logging
import requests
from typing import Dict, Any, List, Generator, Optional
from google import genai
from google.genai import types

from ghl_client import GHLSubAccountClient

logger = logging.getLogger(__name__)

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
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider": "gemini",
        "category": "Google Gemini",
        "badge": "High Speed",
        "supports_tools": True,
        "description": "Optimized for quick turnaround CRM tasks and automated workflows."
    },
    {
        "id": "gemini-1.5-pro",
        "name": "Gemini 1.5 Pro",
        "provider": "gemini",
        "category": "Google Gemini",
        "badge": "Deep Reasoning",
        "supports_tools": True,
        "description": "High-capacity reasoning engine for complex multi-step CRM setups."
    },
    {
        "id": "gemini-1.5-flash",
        "name": "Gemini 1.5 Flash",
        "provider": "gemini",
        "category": "Google Gemini",
        "badge": "Stable",
        "supports_tools": True,
        "description": "Production workhorse model for high volume lead operations."
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
        model_name: str = "gemini-2.0-flash"
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Processes prompt, determines tool calls, executes GHL API commands, and yields SSE stream updates.
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

        system_instruction = f"""You are an Autonomous GoHighLevel (GHL) Sub-Account AI Strategy & Action Execution Agent.
1. When a GHL Sub-Account IS connected (Location ID: {location_id}), invoke the appropriate GHL API tools to create/manage contacts, pipelines, tags, custom fields, tasks, notes, and messages.
2. When NO GHL Sub-Account is connected, function as an expert AI Copilot. Provide complete marketing blueprints, HTML/CSS landing page code, lead form code, email/SMS sequences, and CRM architectures directly in clean markdown without attempting API tool calls.
3. Always report clean, formatted summaries with code blocks and bullet points."""

        if provider == "gemini":
            yield from self._execute_gemini(prompt, ghl, is_ghl_connected, system_instruction, model_name, location_id, access_token)
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
                access_token=access_token
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
                extra_headers={
                    "HTTP-Referer": "http://127.0.0.1:7861",
                    "X-Title": "Conversation AI Copilot"
                }
            )
        else:
            yield {"type": "chunk", "text": f"⚠️ **Unsupported Provider:** {provider}"}

    def _execute_gemini(
        self,
        prompt: str,
        ghl: GHLSubAccountClient,
        is_ghl_connected: bool,
        system_instruction: str,
        model_name: str,
        location_id: str,
        access_token: str
    ) -> Generator[Dict[str, Any], None, None]:
        if not self.gemini_client:
            yield {"type": "chunk", "text": "⚠️ **Error:** Gemini API Key is not configured on server."}
            return

        candidate_models = [model_name]
        for m in ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
            if m not in candidate_models:
                candidate_models.append(m)

        response = None
        last_exception = None

        for mod in candidate_models:
            try:
                config_args = {
                    "system_instruction": system_instruction,
                    "temperature": 0.1
                }
                if is_ghl_connected:
                    config_args["tools"] = [{"function_declarations": GHL_TOOLS_DECLARATIONS}]

                response = self.gemini_client.models.generate_content(
                    model=mod,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config_args)
                )
                last_exception = None
                break
            except Exception as e_mod:
                last_exception = e_mod
                logger.warning(f"Gemini model {mod} failed: {e_mod}, trying next fallback...")

        if response is None or last_exception is not None:
            yield {"type": "chunk", "text": f"⚠️ **Gemini Execution Error:** {str(last_exception)}"}
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

                yield {"type": "chunk", "text": synth_text}
            else:
                yield {"type": "chunk", "text": response.text or "How can I assist you with your GHL Sub-Account?"}

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
        extra_headers: Optional[Dict[str, str]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        if not api_key:
            yield {"type": "chunk", "text": f"⚠️ **Error:** {provider_name} API Key is not configured on the server."}
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        if extra_headers:
            headers.update(extra_headers)

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1500
        }

        # Find if model supports tools
        model_meta = next((m for m in MODELS_CATALOG if m["id"] == model_name), None)
        can_call_tools = is_ghl_connected and (model_meta.get("supports_tools", True) if model_meta else True)

        if can_call_tools:
            payload["tools"] = get_openai_tools_schema()
            payload["tool_choice"] = "auto"

        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=45)
            if resp.status_code != 200:
                err_body = resp.text
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message", err_body)
                except Exception:
                    err_msg = err_body
                yield {"type": "chunk", "text": f"⚠️ **{provider_name} API Error ({resp.status_code}):** {err_msg}"}
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

                    yield {"type": "tool_start", "name": tool_name, "args": tool_args}
                    result = self._dispatch_tool_call(ghl, tool_name, tool_args, location_id, access_token)
                    yield {"type": "tool_result", "name": tool_name, "result": result}

                    msg = result.get("message") or result.get("error") or json.dumps(result)
                    tool_results_summary.append(f"Tool `{tool_name}` result: {msg}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", "call_1"),
                        "content": json.dumps(result)
                    })

                # Follow-up synthesis pass
                synthesis_payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 1000
                }
                try:
                    synth_resp = requests.post(api_url, headers=headers, json=synthesis_payload, timeout=30)
                    if synth_resp.status_code == 200:
                        synth_data = synth_resp.json()
                        synth_text = synth_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        if synth_text:
                            yield {"type": "chunk", "text": synth_text}
                            return
                except Exception:
                    pass

                # Fallback summary if follow-up failed
                yield {"type": "chunk", "text": "✅ **Action Execution Complete:**\n\n" + "\n".join(f"- {s}" for s in tool_results_summary)}
            else:
                # Text reply
                content = message.get("content", "")
                yield {"type": "chunk", "text": content or "How can I assist you with your GoHighLevel Sub-Account?"}

        except requests.exceptions.Timeout:
            yield {"type": "chunk", "text": f"⚠️ **Timeout:** {provider_name} server took too long to respond. Please try again."}
        except Exception as e:
            logger.error(f"{provider_name} request failed: {e}", exc_info=True)
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
