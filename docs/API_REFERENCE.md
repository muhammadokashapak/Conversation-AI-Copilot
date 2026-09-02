# 🔌 API Reference Manual
## Conversation AI Copilot for GoHighLevel (GHL)

This document provides a comprehensive REST and Server-Sent Events (SSE) API specification for the **Conversation AI Copilot** backend server.

---

## 1. General Information

- **Base URL**: `http://127.0.0.1:7861` (Local) or your production domain.
- **Content-Type**: `application/json` (except SSE endpoints which return `text/event-stream`).
- **CORS**: Enabled for all origins (`*`) by default.
- **Authentication**: GHL sub-account operations accept `location_id` and `access_token` in request bodies. AI Provider keys are configured securely on the server via `.env`.

---

## 2. Server & System Endpoints

### 2.1 Health Check
Checks if the FastAPI server is online and checks provider key configuration status.

- **Method**: `GET`
- **Route**: `/health`
- **Request Parameters**: None

#### Response (`200 OK`):
```json
{
  "status": "online",
  "service": "Conversation AI Copilot",
  "port": 7861,
  "providers": {
    "gemini": true,
    "groq": true,
    "rapidapi": false
  }
}
```

---

### 2.2 Available AI Models Catalog
Fetches the catalog of supported models across Google Gemini, Groq Cloud, and OpenRouter, enriched with real-time daily quota and usage statistics.

- **Method**: `GET`
- **Route**: `/api/models`
- **Request Parameters**: None

#### Response (`200 OK`):
```json
{
  "models": [
    {
      "id": "gemini-3.6-flash",
      "name": "Gemini 3.6 Flash (Recommended)",
      "provider": "gemini",
      "category": "Google Gemini",
      "badge": "✨ 1M TPM • Tools",
      "supports_tools": true,
      "description": "State-of-the-art multimodal Gemini model with native GHL function calling.",
      "usage": {
        "daily_requests": 12,
        "daily_limit": 1500,
        "daily_tokens": 4520,
        "total_requests": 84,
        "total_tokens": 32150,
        "usage_percentage": 0.8,
        "remaining_percentage": 99.2,
        "status": "Healthy / High Quota",
        "health_color": "#10b981",
        "last_used": "2026-09-02T18:30:15Z"
      }
    },
    {
      "id": "groq/compound-mini",
      "name": "Groq Compound Mini",
      "provider": "groq",
      "category": "Groq Ultra-Fast",
      "badge": "⚡ 70k TPM Ultra",
      "supports_tools": true,
      "description": "High-throughput Groq Compound model with ~70k TPM capacity.",
      "usage": { ... }
    }
  ],
  "active_providers": {
    "gemini": true,
    "groq": true,
    "rapidapi": false
  },
  "default_model": "gemini-3.6-flash"
}
```

---

### 2.3 Global Usage Statistics
Returns detailed usage, TPM, and daily metrics across all models.

- **Method**: `GET`
- **Route**: `/api/usage-stats`
- **Response (`200 OK`)**:
```json
{
  "success": true,
  "stats": {
    "gemini-3.6-flash": {
      "daily_requests": 14,
      "daily_limit": 1500,
      "daily_tokens": 6200,
      "usage_percentage": 0.93,
      "remaining_percentage": 99.07
    }
  }
}
```

---

### 2.4 OpenRouter Key Pool Status
Polls credit status and active rotation state for the OpenRouter API key pool.

- **Method**: `GET`
- **Route**: `/api/openrouter/pool-status`
- **Response (`200 OK`)**:
```json
{
  "success": true,
  "active_key": "sk-or-v1-987...b1c",
  "pool": [
    {
      "masked": "sk-or-v1-987...b1c",
      "is_active": true,
      "is_depleted": false,
      "total_credits": 10.0,
      "total_usage": 1.45,
      "remaining_credits": 8.55
    }
  ]
}
```

---

## 3. GoHighLevel (GHL) Management Endpoints

All GHL management endpoints expect JSON payloads with your sub-account credentials.

### 3.1 Verify Sub-Account Credentials
Validates the Location ID and Private Integration Bearer Token against GoHighLevel's `/locations/{id}` API.

- **Method**: `POST`
- **Route**: `/api/ghl/verify-token`
- **Body**:
```json
{
  "location_id": "loc_abc123xyz",
  "access_token": "pit-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```
- **Response (Success `200 OK`)**:
```json
{
  "success": true,
  "location_name": "IronPulse Fitness Austin",
  "message": "Successfully connected to GHL Sub-Account: IronPulse Fitness Austin"
}
```
- **Response (Failure `200 OK`)**:
```json
{
  "success": false,
  "message": "GHL API Error (401): Invalid or expired access token."
}
```

---

### 3.2 Fetch Sub-Account Contacts
Fetches contacts list from the target sub-account.

- **Method**: `POST`
- **Route**: `/api/ghl/contacts`
- **Body**:
```json
{
  "location_id": "loc_abc123xyz",
  "access_token": "pit-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

---

### 3.3 Create Contact (Manual)
Directly creates a contact in GoHighLevel without conversational prompting.

- **Method**: `POST`
- **Route**: `/api/ghl/create-contact`
- **Body**:
```json
{
  "location_id": "loc_abc123xyz",
  "access_token": "pit-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "first_name": "Sarah",
  "last_name": "Connor",
  "email": "sarah.connor@example.com",
  "phone": "+15125550198",
  "tag": "Website Lead"
}
```
- **Response (`200 OK`)**:
```json
{
  "success": true,
  "data": {
    "contact": {
      "id": "cnt_998877",
      "firstName": "Sarah",
      "lastName": "Connor",
      "email": "sarah.connor@example.com",
      "phone": "+15125550198"
    }
  },
  "message": "✅ Contact 'Sarah Connor' created successfully."
}
```

---

### 3.4 Fetch Pipelines
Fetches all sales and opportunity pipelines along with their stages.

- **Method**: `POST`
- **Route**: `/api/ghl/pipelines`
- **Body**:
```json
{
  "location_id": "loc_abc123xyz",
  "access_token": "pit-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

---

### 3.5 Fetch Location Tags
Fetches all configured tags in the sub-account.

- **Method**: `POST`
- **Route**: `/api/ghl/tags`
- **Body**:
```json
{
  "location_id": "loc_abc123xyz",
  "access_token": "pit-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

---

### 3.6 Fetch Custom Fields
Fetches custom contact fields defined in the location.

- **Method**: `POST`
- **Route**: `/api/ghl/custom-fields`
- **Body**:
```json
{
  "location_id": "loc_abc123xyz",
  "access_token": "pit-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

---

### 3.7 Deploy Gym Vertical Architecture Blueprint
Automatically provisions 14 custom fields, 12 tags, and 2 multi-stage retention/sales pipelines in the sub-account.

- **Method**: `POST`
- **Route**: `/api/ghl/setup-gym`
- **Body**:
```json
{
  "location_id": "loc_abc123xyz",
  "access_token": "pit-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```
- **Response (`200 OK`)**:
```json
{
  "success": true,
  "summary": {
    "custom_fields_created": 14,
    "tags_created": 12,
    "pipelines_created": 2
  },
  "details": "✅ Gym & Fitness Architecture successfully deployed."
}
```

---

## 4. Agent Execution & SSE Streaming Endpoint

### 4.1 Chat Agent Execution Stream
The primary conversational agent endpoint. Takes a natural language prompt, evaluates intent, calls GHL tools when needed, and streams the output via Server-Sent Events.

- **Method**: `POST`
- **Route**: `/api/chat-agent`
- **Headers**:
  - `Content-Type: application/json`
  - `Accept: text/event-stream`

#### Request Body Schema (`AgentChatRequest`):

| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `prompt` | `string` | **Yes** | — | User input or command for the agent. |
| `location_id` | `string` | No | `""` | GHL Location ID (if GHL actions are needed). |
| `access_token` | `string` | No | `""` | GHL Bearer Token (if GHL actions are needed). |
| `selected_model` | `string` | No | `"gemini-3.6-flash"` | Target model identifier from catalog. |
| `history` | `array` | No | `[]` | List of prior messages `[{"role": "user"|"assistant", "content": "..."}]`. |
| `attachments` | `array` | No | `[]` | List of attached files or images. |

#### Attachment Object Schema (`AttachmentItem`):
```json
{
  "name": "brand-guidelines.pdf",
  "type": "file",
  "mime_type": "application/pdf",
  "data": "data:application/pdf;base64,...",
  "size": 1048576
}
```

#### SSE Event Payloads Emitted by Stream:

1. **Chunk Event** (Rendered in real-time as markdown):
   ```json
   data: {"type": "chunk", "text": "Building your custom funnel structure..."}
   ```
2. **Tool Invocation Event** (Triggers active badge):
   ```json
   data: {"type": "tool_call", "name": "create_pipeline", "args": {"name": "VIP Fitness Funnel", "stages": ["New Lead", "Trial Booked", "Member Won"]}}
   ```
3. **Tool Result Event** (Badge updates to success or failure):
   ```json
   data: {"type": "tool_result", "name": "create_pipeline", "result": {"success": true, "data": {"id": "pip_123"}}, "success": true}
   ```
4. **Usage Update Event**:
   ```json
   data: {"type": "usage_update", "model": "gemini-3.6-flash", "stats": {"daily_requests": 15, "daily_tokens": 1240}}
   ```
5. **Stream Done Event**:
   ```json
   data: {"type": "done"}
   ```

---

## 5. Command-Line Examples (cURL)

### Health Check:
```bash
curl -X GET http://127.0.0.1:7861/health
```

### Verify GHL Sub-Account:
```bash
curl -X POST http://127.0.0.1:7861/api/ghl/verify-token \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "YOUR_LOCATION_ID",
    "access_token": "YOUR_BEARER_TOKEN"
  }'
```

### Prompt Agent with SSE Streaming:
```bash
curl -N -X POST http://127.0.0.1:7861/api/chat-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a new contact named Alex Mercer with email alex@mercer.com and tag VIP",
    "location_id": "YOUR_LOCATION_ID",
    "access_token": "YOUR_BEARER_TOKEN",
    "selected_model": "gemini-3.6-flash"
  }'
```
