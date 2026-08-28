import os
import json
import logging
from typing import Dict, Any, List, Generator
from google import genai
from google.genai import types

from ghl_client import GHLSubAccountClient

logger = logging.getLogger(__name__)

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
                "body": {"type": "STRING", "description": "Note content text"}
            },
            "required": ["contact_id", "body"]
        }
    },
    {
        "name": "setup_gym_subaccount",
        "description": "Deploy the complete, production-ready Gym & Fitness Center architecture (17 custom fields, 20 tags, 2 pipelines) to the GHL Sub-Account",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    }
]


class GHLAgentExecutionEngine:
    """
    Executes user prompts against GHL API v2 using Gemini Function Calling.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

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
        if not self.client:
            yield {"type": "chunk", "text": "⚠️ **Error:** Gemini API Key is not configured on server."}
            return

        ghl = GHLSubAccountClient(location_id=location_id, access_token=access_token)
        
        # Check connection status first if token/location given
        if location_id and access_token:
            conn_status = ghl.verify_connection()
            if not conn_status.get("success"):
                yield {"type": "tool_start", "name": "verify_connection", "args": {"location_id": location_id}}
                yield {"type": "tool_result", "name": "verify_connection", "result": conn_status}
                yield {"type": "chunk", "text": f"⚠️ **GHL Connection Error:** {conn_status.get('message')}"}
                return

        is_ghl_connected = bool(location_id and access_token)

        system_instruction = f"""You are an Autonomous GoHighLevel (GHL) Sub-Account AI Strategy & Action Execution Agent.
1. When a GHL Sub-Account IS connected (Location ID: {location_id}), invoke the appropriate GHL API tools to create/manage contacts, pipelines, tags, custom fields, and messages.
2. When NO GHL Sub-Account is connected, function as an expert AI Copilot. Provide complete marketing blueprints, HTML/CSS landing page code, lead form code, email/SMS sequences, and CRM architectures directly in markdown without attempting API tool calls.
3. Always report clean, formatted summaries with code blocks and bullet points."""

        # Model fallback chain (Prioritizing active Gemini 3.6 & 3.5 models)
        candidate_models = [model_name]
        for m in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest", "gemini-pro-latest", "gemini-2.5-flash"]:
            if m not in candidate_models:
                candidate_models.append(m)

        response = None
        used_model = model_name
        last_exception = None

        for mod in candidate_models:
            try:
                config_args = {
                    "system_instruction": system_instruction,
                    "temperature": 0.1
                }
                if is_ghl_connected:
                    config_args["tools"] = [{"function_declarations": GHL_TOOLS_DECLARATIONS}]

                response = self.client.models.generate_content(
                    model=mod,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config_args)
                )
                used_model = mod
                last_exception = None
                break
            except Exception as e_mod:
                last_exception = e_mod
                logger.warning(f"Model {mod} failed: {e_mod}, trying next fallback model...")

        if response is None or last_exception is not None:
            yield {"type": "chunk", "text": f"⚠️ **Agent Execution Error:** {str(last_exception)}"}
            return

        try:
            # Check if Gemini wants to call tools
            function_calls = []
            if response.function_calls:
                function_calls = response.function_calls

            if function_calls:
                tool_results_summary = []
                for fc in function_calls:
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}

                    yield {"type": "tool_start", "name": tool_name, "args": tool_args}
                    logger.info(f"⚡ Agent executing tool: {tool_name} with args {tool_args}")

                    # Check credentials before API call
                    if not location_id or not access_token:
                        result = {
                            "success": False,
                            "error": "Location ID & Access Token missing. Please click 'Connect Location' at the top bar to connect your GHL Sub-Account."
                        }
                    else:
                        # Dispatch tool call to GHL client
                        result = {"success": False, "error": "Unknown tool"}
                        if tool_name == "create_contact":
                            result = ghl.create_contact(**tool_args)
                        elif tool_name == "search_contacts":
                            result = ghl.search_contacts(**tool_args)
                        elif tool_name == "create_pipeline":
                            result = ghl.create_pipeline(**tool_args)
                        elif tool_name == "get_pipelines":
                            result = ghl.get_pipelines()
                        elif tool_name == "create_opportunity":
                            result = ghl.create_opportunity(**tool_args)
                        elif tool_name == "create_tag":
                            result = ghl.create_tag(**tool_args)
                        elif tool_name == "create_custom_field":
                            result = ghl.create_custom_field(**tool_args)
                        elif tool_name == "send_conversation_message":
                            result = ghl.send_conversation_message(**tool_args)
                        elif tool_name == "create_contact_task":
                            result = ghl.create_contact_task(**tool_args)
                        elif tool_name == "create_contact_note":
                            result = ghl.create_contact_note(**tool_args)
                        elif tool_name == "setup_gym_subaccount":
                            result = ghl.setup_gym_subaccount()

                    yield {"type": "tool_result", "name": tool_name, "result": result}

                    msg = result.get("message") or result.get("error") or json.dumps(result)
                    tool_results_summary.append(f"Tool `{tool_name}` result: {msg}")

                # Synthesis Pass after tool execution
                synthesis_prompt = f"User Request: {prompt}\n\nActions Taken:\n" + "\n".join(tool_results_summary) + "\n\nProvide a friendly final response confirming the action taken in the GHL Sub-Account."
                synth_text = "Action execution complete."
                for mod in candidate_models:
                    try:
                        synth_res = self.client.models.generate_content(
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
                # Direct text response if no tool call required
                yield {"type": "chunk", "text": response.text or "How can I assist you with your GHL Sub-Account?"}

        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            yield {"type": "chunk", "text": f"⚠️ **Agent Execution Error:** {str(e)}"}
