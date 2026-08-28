import requests
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class GHLSubAccountClient:
    """
    GoHighLevel REST API v2 SDK for Sub-Account (Location) Asset Creation & Management.
    Official Base URL: https://services.leadconnectorhq.com
    API Version Header: 2021-07-28
    """
    BASE_URL = "https://services.leadconnectorhq.com"
    API_VERSION = "2021-07-28"

    def __init__(self, location_id: str, access_token: str):
        self.location_id = location_id.strip() if location_id else ""
        self.access_token = access_token.strip() if access_token else ""

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Version": self.API_VERSION,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def verify_connection(self) -> Dict[str, Any]:
        """Verify if Location ID and Access Token are valid."""
        if not self.location_id or not self.access_token:
            return {"success": False, "message": "Missing Location ID or Access Token."}

        url = f"{self.BASE_URL}/locations/{self.location_id}"
        try:
            res = requests.get(url, headers=self._get_headers(), timeout=10)
            if res.status_code == 200:
                data = res.json()
                loc_name = data.get("location", {}).get("name") or "Sub-Account"
                return {"success": True, "location_name": loc_name, "message": f"Successfully connected to GHL Sub-Account: {loc_name}"}
            else:
                err_detail = res.json().get("message", res.text) if res.text else res.reason
                return {"success": False, "message": f"GHL API Error ({res.status_code}): {err_detail}"}
        except Exception as e:
            return {"success": False, "message": f"Connection Exception: {str(e)}"}

    def create_contact(
        self,
        first_name: str,
        last_name: str = "",
        email: str = "",
        phone: str = "",
        tags: Optional[List[str]] = None,
        custom_fields: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create a new Contact in the GHL Sub-Account."""
        url = f"{self.BASE_URL}/contacts/"
        payload = {
            "locationId": self.location_id,
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": phone
        }
        if tags:
            payload["tags"] = tags
        if custom_fields:
            payload["customFields"] = custom_fields

        try:
            res = requests.post(url, headers=self._get_headers(), json=payload, timeout=12)
            if res.status_code in [200, 201]:
                return {"success": True, "data": res.json(), "message": f"✅ Contact '{first_name} {last_name}'.strip() created successfully."}
            else:
                err_detail = res.json().get("message", res.text)
                return {"success": False, "error": f"HTTP {res.status_code}: {err_detail}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_contacts(self, query: str) -> Dict[str, Any]:
        """Search contacts by query string."""
        url = f"{self.BASE_URL}/contacts/"
        params = {"locationId": self.location_id, "query": query}
        try:
            res = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            else:
                return {"success": False, "error": res.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_pipeline(self, name: str, stages: List[str]) -> Dict[str, Any]:
        """Create a new Opportunity Pipeline with custom stages."""
        url = f"{self.BASE_URL}/opportunities/pipelines/"
        formatted_stages = [{"name": st, "position": idx} for idx, st in enumerate(stages)]
        payload = {
            "locationId": self.location_id,
            "name": name,
            "stages": formatted_stages
        }
        try:
            res = requests.post(url, headers=self._get_headers(), json=payload, timeout=12)
            if res.status_code in [200, 201]:
                return {"success": True, "data": res.json(), "message": f"✅ Pipeline '{name}' created with {len(stages)} stages."}
            else:
                return {"success": False, "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_pipelines(self) -> Dict[str, Any]:
        """Fetch all Opportunity Pipelines in location."""
        url = f"{self.BASE_URL}/opportunities/pipelines/"
        params = {"locationId": self.location_id}
        try:
            res = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            else:
                return {"success": False, "error": res.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_opportunity(
        self,
        pipeline_id: str,
        stage_id: str,
        title: str,
        status: str = "open",
        monetary_value: float = 0.0,
        contact_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an Opportunity / Deal in a pipeline stage."""
        url = f"{self.BASE_URL}/opportunities/"
        payload = {
            "locationId": self.location_id,
            "pipelineId": pipeline_id,
            "pipelineStageId": stage_id,
            "name": title,
            "status": status,
            "monetaryValue": monetary_value
        }
        if contact_id:
            payload["contactId"] = contact_id

        try:
            res = requests.post(url, headers=self._get_headers(), json=payload, timeout=12)
            if res.status_code in [200, 201]:
                return {"success": True, "data": res.json(), "message": f"✅ Opportunity '{title}' created successfully."}
            else:
                return {"success": False, "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_tag(self, tag_name: str) -> Dict[str, Any]:
        """Create a new tag for the GHL Sub-Account."""
        url = f"{self.BASE_URL}/locations/{self.location_id}/tags"
        payload = {"name": tag_name}
        try:
            res = requests.post(url, headers=self._get_headers(), json=payload, timeout=10)
            if res.status_code in [200, 201]:
                return {"success": True, "data": res.json(), "message": f"✅ Tag '{tag_name}' created successfully."}
            else:
                return {"success": False, "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_custom_field(self, name: str, data_type: str = "TEXT") -> Dict[str, Any]:
        """Create a Custom Field (TEXT, NUMBER, SINGLE_OPTIONS, etc.) in GHL."""
        url = f"{self.BASE_URL}/locations/{self.location_id}/custom-fields"
        payload = {
            "name": name,
            "dataType": data_type.upper(),
            "placeholder": f"Enter {name}"
        }
        try:
            res = requests.post(url, headers=self._get_headers(), json=payload, timeout=10)
            if res.status_code in [200, 201]:
                return {"success": True, "data": res.json(), "message": f"✅ Custom Field '{name}' ({data_type}) created."}
            else:
                return {"success": False, "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_conversation_message(self, contact_id: str, message: str, type_: str = "SMS") -> Dict[str, Any]:
        """Send an SMS or Email message to a contact via GHL conversations endpoint."""
        url = f"{self.BASE_URL}/conversations/messages"
        payload = {
            "type": type_.upper(),
            "contactId": contact_id,
            "message": message
        }
        try:
            res = requests.post(url, headers=self._get_headers(), json=payload, timeout=10)
            if res.status_code in [200, 201]:
                return {"success": True, "data": res.json(), "message": f"✅ Message sent to contact ID {contact_id} via {type_}."}
            else:
                return {"success": False, "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_tags(self) -> Dict[str, Any]:
        """Fetch all Location Tags."""
        url = f"{self.BASE_URL}/locations/{self.location_id}/tags"
        try:
            res = requests.get(url, headers=self._get_headers(), timeout=10)
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            else:
                return {"success": False, "error": res.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_custom_fields(self) -> Dict[str, Any]:
        """Fetch all Custom Fields in location."""
        url = f"{self.BASE_URL}/locations/{self.location_id}/custom-fields"
        try:
            res = requests.get(url, headers=self._get_headers(), timeout=10)
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            else:
                return {"success": False, "error": res.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_workflows(self) -> Dict[str, Any]:
        """Fetch all Workflows in location."""
        url = f"{self.BASE_URL}/workflows/"
        params = {"locationId": self.location_id}
        try:
            res = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            else:
                return {"success": False, "error": res.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_contact_task(self, contact_id: str, title: str, due_date: str = "") -> Dict[str, Any]:
        """Create a Task for a Contact."""
        url = f"{self.BASE_URL}/contacts/{contact_id}/tasks"
        payload = {"title": title, "completed": False}
        if due_date:
            payload["dueDate"] = due_date
        try:
            res = requests.post(url, headers=self._get_headers(), json=payload, timeout=10)
            if res.status_code in [200, 201]:
                return {"success": True, "data": res.json(), "message": f"✅ Task '{title}' added to contact ID {contact_id}."}
            else:
                return {"success": False, "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_contact_note(self, contact_id: str, body: str) -> Dict[str, Any]:
        """Add an internal note to a contact."""
        url = f"{self.BASE_URL}/contacts/{contact_id}/notes"
        payload = {"body": body}
        try:
            res = requests.post(url, headers=self._get_headers(), json=payload, timeout=10)
            if res.status_code in [200, 201]:
                return {"success": True, "data": res.json(), "message": f"✅ Note added to contact ID {contact_id}."}
            else:
                return {"success": False, "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def setup_gym_subaccount(self) -> Dict[str, Any]:
        """Automated Setup of Gym & Fitness Center Sub-Account Architecture (Custom Fields, Tags, Pipelines)."""
        from gym_architecture import GYM_CUSTOM_FIELDS_SCHEMA, GYM_TAGS_TAXONOMY, GYM_SALES_PIPELINE, GYM_RETENTION_PIPELINE

        created_fields = 0
        created_tags = 0
        created_pipelines = 0
        errors = []

        # 1. Create Custom Fields
        for field in GYM_CUSTOM_FIELDS_SCHEMA:
            res = self.create_custom_field(name=field["name"], data_type=field.get("dataType", "TEXT"))
            if res.get("success"):
                created_fields += 1
            else:
                errors.append(f"Field '{field['name']}': {res.get('error')}")

        # 2. Create Tags
        for tag in GYM_TAGS_TAXONOMY:
            res = self.create_tag(tag_name=tag)
            if res.get("success"):
                created_tags += 1
            else:
                errors.append(f"Tag '{tag}': {res.get('error')}")

        # 3. Create Pipelines
        p1 = self.create_pipeline(name=GYM_SALES_PIPELINE["name"], stages=GYM_SALES_PIPELINE["stages"])
        if p1.get("success"): created_pipelines += 1
        else: errors.append(f"Sales Pipeline: {p1.get('error')}")

        p2 = self.create_pipeline(name=GYM_RETENTION_PIPELINE["name"], stages=GYM_RETENTION_PIPELINE["stages"])
        if p2.get("success"): created_pipelines += 1
        else: errors.append(f"Retention Pipeline: {p2.get('error')}")

        return {
            "success": True,
            "created_fields": created_fields,
            "created_tags": created_tags,
            "created_pipelines": created_pipelines,
            "errors": errors,
            "message": f"✅ Gym Sub-Account Architecture Setup Complete: {created_fields} Fields, {created_tags} Tags, {created_pipelines} Pipelines deployed."
        }
