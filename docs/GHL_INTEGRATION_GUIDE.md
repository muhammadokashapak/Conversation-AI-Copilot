# 🛠️ GoHighLevel (GHL) Integration & Architecture Guide
## Conversation AI Copilot for GoHighLevel (GHL)

This guide provides technical instructions for integrating the **Conversation AI Copilot** with GoHighLevel sub-accounts, obtaining the appropriate API credentials, understanding required OAuth/Private Integration scopes, and deploying vertical CRM architectures.

---

## 1. HighLevel API Architecture Overview

The Copilot communicates natively with **GoHighLevel REST API v2**.

- **Base Endpoint**: `https://services.leadconnectorhq.com`
- **Required Protocol Header**: `Version: 2021-07-28`
- **Authorization Header**: `Authorization: Bearer <ACCESS_TOKEN>`
- **Target Context**: Sub-Account (Location) Level. All mutations and queries require a valid `locationId`.

---

## 2. Authentication: Private Integration Token (Recommended)

For direct sub-account automation, HighLevel provides **Private Integrations**, which issue a dedicated Bearer Token bound directly to your sub-account.

### How to Generate a Private Integration Token:

1. Log into your **GoHighLevel Sub-Account** (or Agency Switcher ➡️ Sub-Account).
2. Navigate to **Settings** (bottom left) ➡️ **Private Integrations** (or Developer / Integrations).
3. Click **+ Create Private Integration**.
4. Name your integration: `Conversation AI Copilot`.
5. Select the required **API Scopes** (see matrix below).
6. Click **Save / Generate Key**.
7. Copy the generated **Location ID** and **Access Token** (starts with `pit-`).
8. Paste these credentials into the Copilot UI (via the **Connect GHL Sub-Account** modal) or pass them in API requests.

---

## 3. Required API Scopes Matrix

To enable all autonomous capabilities, grant the following scopes to your Private Integration:

| Feature / Tool Area | Required HighLevel Scopes | Permission Type |
| :--- | :--- | :--- |
| **Contacts Management** | `contacts.readonly`, `contacts.write` | Read & Write |
| **Pipelines & Opportunities** | `opportunities.readonly`, `opportunities.write` | Read & Write |
| **Custom Fields & Values** | `locations/customFields.readonly`, `locations/customFields.write` | Read & Write |
| **Tags Taxonomy** | `locations/tags.readonly`, `locations/tags.write` | Read & Write |
| **Conversations (SMS/Email)** | `conversations.readonly`, `conversations.write`, `conversations/message.write` | Read & Write |
| **Tasks** | `contacts/tasks.readonly`, `contacts/tasks.write` | Read & Write |
| **Notes** | `contacts/notes.readonly`, `contacts/notes.write` | Read & Write |
| **Location Profile** | `locations.readonly` | Read Only (Verification) |

---

## 4. Supported Action Tools & Schemas

The agent runtime evaluates user prompts and dynamically calls the following GHL tools:

### 4.1 `create_contact`
- **Endpoint**: `POST /contacts/`
- **Parameters**:
  - `first_name` (*string*, required)
  - `last_name` (*string*, optional)
  - `email` (*string*, optional)
  - `phone` (*string*, optional - strictly formatted to E.164: e.g. `+15551234567`)
  - `tags` (*array of strings*, optional)
  - `custom_fields` (*array of dicts*, optional)
- **Engine Rules**:
  - Automatically avoids sending duplicate or redundant `name` properties when `first_name` and `last_name` are present.
  - Formats phone numbers to international E.164 standard.

### 4.2 `search_contacts`
- **Endpoint**: `GET /contacts/?locationId={locationId}&query={query}`
- **Parameters**: `query` (*string*, required) - matches against name, email, or phone.

### 4.3 `create_pipeline` & `get_pipelines`
- **Endpoints**:
  - `POST /opportunities/pipelines/`
  - `GET /opportunities/pipelines/?locationId={locationId}`
- **Parameters**: `name` (*string*), `stages` (*list of strings*).
- **Positioning**: Automatically assigns zero-indexed positional ordering to stages (`[{"name": "Stage A", "position": 0}, {"name": "Stage B", "position": 1}]`).

### 4.4 `create_opportunity`
- **Endpoint**: `POST /opportunities/`
- **Parameters**:
  - `pipeline_id` (*string*, required)
  - `stage_id` (*string*, required)
  - `title` (*string*, required)
  - `monetary_value` (*float*, optional)
  - `status` (*string*, default `"open"`, options: `open`, `won`, `lost`, `abandoned`)

### 4.5 `create_custom_field` & `create_tag`
- **Endpoints**:
  - `POST /locations/{locationId}/customFields`
  - `POST /locations/{locationId}/tags`
- **Supported Data Types**: `TEXT`, `NUMBER`, `DATE`, `SINGLE_OPTIONS`.

### 4.6 `send_conversation_message`
- **Endpoint**: `POST /conversations/messages`
- **Parameters**: `contact_id` (*string*), `message` (*string*), `type_` (`"SMS"` or `"Email"`).

### 4.7 `create_contact_task` & `create_contact_note`
- **Endpoints**:
  - `POST /contacts/{contact_id}/tasks`
  - `POST /contacts/{contact_id}/notes`
- **Parameters**: Task titles, ISO due dates, and internal team note bodies.

---

## 5. Senior GHL Solutions Architect Engineering Rules

The Copilot's prompt and tool engine enforces **29 strict architectural rules** modeled after senior SaaS technical leadership:

1. **Strict REST v2 Endpoint Adherence**: Always targets `https://services.leadconnectorhq.com` with `Version: 2021-07-28`. Never calls deprecated v1 routes.
2. **Authentication Hygiene**: Explicitly differentiates between sub-account Private Integration Tokens and agency OAuth 2.0 app grants.
3. **Payload Sanitization**: Enforces valid E.164 phone formats and removes redundant full-name properties when discrete names are supplied.
4. **Failure-Mode Awareness**: Detects and reports common platform gotchas (e.g. duplicate contact merging rules, rate limits, unverified domain sending blocks).
5. **Zero Fabrication & Query Scope**: Only recommends verified native HighLevel features or confirmed API endpoints. Rejects speculative feature hallucination.
6. **Single-Pass Completeness**: Delivers complete, self-contained architectures without fragmented or unclosed code blocks.

---

## 6. Pre-Packaged Vertical Architecture: Gym & Fitness Centers

The system includes a production blueprint (`gym_architecture.py`) designed for fitness clubs, boutique studios, and gym sub-accounts.

### 6.1 Custom Fields Blueprint (14 Fields):
- `Primary Fitness Goal` (Single Options: Weight Loss, Muscle Building, Athletic Performance, etc.)
- `Exercise Experience` (Single Options: Beginner, Intermediate, Advanced)
- `Exercise Limitations` (Single Options: Yes / No)
- `Limitation Category` (Single Options: Knee, Shoulder, Back/Core, Cardio)
- `Trainer Safety Notes` (Text)
- `Preferred Workout Time` (Single Options: Early Morning, Mid-Day, Evening)
- `Lead Score` (Number)
- `Lead Tier` (Single Options: Cold, Warm, Hot)
- `Score Last Evaluated Date` (Date)
- `Membership Plan Type` (Single Options: Month-to-Month, Annual VIP, 1-on-1 PT)
- `Membership Status` (Single Options: Prospect, Trial Active, Active Member, Frozen, Churned)
- `Trial End Date` (Date)
- `Last Check-in Date` (Date)
- `Total Check-ins Completed` (Number)

### 6.2 Pipelines & Lifecycle Stages:
1. **Gym Sales & Trial Conversion Pipeline**:
   - `New Prospect Inquiry`
   - `Free Pass / Consultation Claimed`
   - `Discovery Call / Tour Booked`
   - `Tour Completed (No Sale)`
   - `Trial Active (Day 1-7)`
   - `VIP Member Converted (Won)`
   - `Unresponsive / Recycle (Lost)`
2. **Member Retention & Attendance Pipeline**:
   - `Onboarding Week 1`
   - `Active Member (Green / Consistent)`
   - `Attendance Dip (< 2 Visits in 14 Days)`
   - `At-Risk / Inactive Flagged`
   - `Save Protocol Engaged`
   - `Churned / Frozen`

---

## 7. Connecting via UI or API

Once your Location ID and Access Token are obtained, you can connect through:
1. **Dashboard UI**: Click the **⚙️ Connect GHL** button in the top navigation bar, enter your credentials, and click **Verify & Connect**.
2. **Direct API**: Include `"location_id"` and `"access_token"` in requests sent to `/api/chat-agent`.
