# GHL Sub-Account Action Execution Agent (`ghl_action_agent`)

An isolated, autonomous AI Action Execution Agent that connects to GoHighLevel (GHL) Sub-Accounts (Locations) via REST API v2 and performs asset creation and management directly from natural language prompts.

## Key Features
- **Isolated Directory**: Lives completely inside `ghl_action_agent/`, keeping your main codebase safe and untouched.
- **Port 7861**: Runs on port 7861 so it can be executed alongside the main app on port 7860.
- **GHL REST API v2 SDK**:
  - `create_contact`: Creates contacts with tags and custom fields.
  - `create_pipeline`: Builds sales pipelines with custom stages.
  - `create_opportunity`: Places deal cards into target pipeline stages.
  - `create_tag`: Creates location-level tags.
  - `create_custom_field`: Creates custom fields (TEXT, NUMBER, DATE, etc.).
  - `send_conversation_message`: Sends SMS/Email messages via GHL conversations.
- **Gemini Function Calling**: Maps natural language prompts to GHL API tools dynamically.
- **Live Tool Badges UI**: Shows real-time execution feedback in chat bubbles (`⚡ Invoking Tool` -> `✅ Tool Result`).

## How to Run

```bash
cd "ghl_action_agent"
python app.py
```

Then open `http://127.0.0.1:7861/` in your browser.
Click **Connect Sub-Account** at the top right to enter your Location ID and Access Token!
