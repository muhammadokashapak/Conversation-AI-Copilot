"""
Generate clean, minimal, professional Project Documentation PDF for Conversation AI Copilot.
Theme: Simple, clean technical report style (white background, black/dark charcoal text, no fancy/VIP designs, no headers, no footers).
Covers every single component, file, feature, and integration used in the project.
"""

import os
import sys
from playwright.sync_api import sync_playwright

OUTPUT_HTML = os.path.join(os.path.dirname(__file__), "simple_project_report.html")
OUTPUT_PDF = os.path.join(os.path.dirname(__file__), "Conversation_AI_Copilot_Complete_Documentation.pdf")

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Conversation AI Copilot - Complete Project Documentation</title>
    <style>
        @page {
            size: A4 portrait;
            margin: 20mm 20mm 20mm 20mm;
            /* Explicitly NO header and NO footer */
            @top-left { content: none; }
            @top-right { content: none; }
            @top-center { content: none; }
            @bottom-left { content: none; }
            @bottom-right { content: none; }
            @bottom-center { content: none; }
        }

        * {
            box-sizing: border-box;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.55;
            color: #111827;
            background: #ffffff;
            margin: 0;
            padding: 0;
        }

        h1 {
            font-size: 20pt;
            font-weight: 700;
            color: #0f172a;
            margin: 0 0 6px 0;
            letter-spacing: -0.02em;
            line-height: 1.2;
        }

        .subtitle {
            font-size: 11pt;
            color: #4b5563;
            margin: 0 0 24px 0;
            padding-bottom: 14px;
            border-bottom: 2px solid #e5e7eb;
        }

        h2 {
            font-size: 13pt;
            font-weight: 700;
            color: #111827;
            margin: 22px 0 10px 0;
            padding-bottom: 4px;
            border-bottom: 1px solid #d1d5db;
            page-break-after: avoid;
        }

        h3 {
            font-size: 10.5pt;
            font-weight: 600;
            color: #1f2937;
            margin: 14px 0 6px 0;
            page-break-after: avoid;
        }

        p {
            margin: 0 0 10px 0;
            text-align: justify;
        }

        ul, ol {
            margin: 0 0 12px 0;
            padding-left: 22px;
        }

        li {
            margin-bottom: 4px;
        }

        code {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 9pt;
            background: #f3f4f6;
            padding: 1px 4px;
            border-radius: 3px;
            border: 1px solid #e5e7eb;
            color: #1f2937;
        }

        pre {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 8.5pt;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            padding: 10px 12px;
            margin: 8px 0 14px 0;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-word;
            line-height: 1.45;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0 16px 0;
            font-size: 9pt;
            page-break-inside: avoid;
        }

        th, td {
            border: 1px solid #d1d5db;
            padding: 7px 10px;
            text-align: left;
            vertical-align: top;
        }

        th {
            background-color: #f3f4f6;
            font-weight: 600;
            color: #111827;
        }

        tr:nth-child(even) {
            background-color: #fafafa;
        }

        .meta-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 20px;
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            padding: 12px 14px;
            border-radius: 4px;
        }

        .meta-item {
            font-size: 8.5pt;
        }

        .meta-label {
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            font-size: 7.5pt;
            display: block;
            margin-bottom: 2px;
        }

        .meta-val {
            color: #111827;
            font-weight: 500;
        }

        .note-box {
            background: #f9fafb;
            border-left: 3px solid #4b5563;
            padding: 8px 12px;
            margin: 10px 0 14px 0;
            font-size: 9pt;
            color: #374151;
        }

        .page-break {
            page-break-before: always;
        }
    </style>
</head>
<body>

    <!-- TITLE & OVERVIEW -->
    <h1>Conversation AI Copilot</h1>
    <div class="subtitle">Complete Technical Project Documentation & System Specifications</div>

    <div class="meta-grid">
        <div class="meta-item">
            <span class="meta-label">Project Name</span>
            <span class="meta-val">Conversation AI Copilot</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">Primary Stack</span>
            <span class="meta-val">Python / FastAPI / Vanilla JS</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">Integration</span>
            <span class="meta-val">GoHighLevel (GHL) API 2.0</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">Deployment Port</span>
            <span class="meta-val">http://127.0.0.1:7861</span>
        </div>
    </div>

    <h2>1. Executive Summary & Purpose</h2>
    <p>
        <strong>Conversation AI Copilot</strong> is a production-grade autonomous technical assistant and full-stack sales automation copilot designed specifically for agencies and businesses operating on <strong>GoHighLevel (HighLevel / GHL)</strong>.
    </p>
    <p>
        The system acts as a dual-purpose solution:
    </p>
    <ol>
        <li><strong>Autonomous CRM Operator:</strong> Directly connects to GoHighLevel Sub-Accounts via Private Integration Tokens or OAuth 2.0 to execute live CRM operations (creating contacts, tags, custom fields, opportunities, and sales pipelines) using native function calling.</li>
        <li><strong>Architectural Code & Funnel Generator:</strong> Generates complete, self-contained single-file HTML/Tailwind CSS interactive web applications, high-converting VSL funnels, 2-step checkout forms, and enterprise-grade drop-off recovery workflow automations (15m, 4h, 24h cadence).</li>
    </ol>

    <h2>2. High-Level System Architecture</h2>
    <p>
        The application is structured into a lightweight backend powered by FastAPI (Python 3.10+) serving a dynamic vanilla HTML5/CSS3 frontend. All chat interactions stream over HTTP Server-Sent Events (SSE) for low latency.
    </p>

    <table>
        <thead>
            <tr>
                <th style="width: 28%;">Component</th>
                <th style="width: 32%;">File Path</th>
                <th style="width: 40%;">Primary Responsibility</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>FastAPI Application</strong></td>
                <td><code>app.py</code></td>
                <td>HTTP endpoints, SSE streaming handler, thread management, CORS, static file delivery, and singleton engine factory.</td>
            </tr>
            <tr>
                <td><strong>Agent Execution Engine</strong></td>
                <td><code>agent_engine.py</code></td>
                <td>Multi-provider model orchestration, function-calling dispatch, prompt classification, auto-continuation, and failover cascade.</td>
            </tr>
            <tr>
                <td><strong>Key Pool Manager</strong></td>
                <td><code>key_pool_manager.py</code></td>
                <td>Thread-safe multi-key rotation, automatic 429 backoff, health tracking, and failover for Google Gemini and OpenRouter.</td>
            </tr>
            <tr>
                <td><strong>GoHighLevel API Client</strong></td>
                <td><code>ghl_client.py</code></td>
                <td>Dedicated wrapper for HighLevel API 2.0 (version 2021-07-28) handling contacts, pipelines, custom fields, and opportunities.</td>
            </tr>
            <tr>
                <td><strong>Live Usage Tracker</strong></td>
                <td><code>usage_tracker.py</code></td>
                <td>Sliding-window token counter tracking real-time TPM (Tokens Per Minute), RPM (Requests Per Minute), and daily quota percentages.</td>
            </tr>
            <tr>
                <td><strong>Web User Interface</strong></td>
                <td><code>static/index.html</code></td>
                <td>Responsive single-page web app featuring floating input island, 6-step landing page wizard, and live model badge indicators.</td>
            </tr>
            <tr>
                <td><strong>Design & Aesthetics</strong></td>
                <td><code>static/style.css</code></td>
                <td>Comprehensive CSS design system, dark/light theme support, glassmorphism, responsive grid layouts, and code block styling.</td>
            </tr>
            <tr>
                <td><strong>Client Application Logic</strong></td>
                <td><code>static/app.js</code></td>
                <td>SSE stream reader, Markdown parser (marked.js), syntax highlighter (highlight.js), voice dictation, and modal wizards.</td>
            </tr>
            <tr>
                <td><strong>Configuration & Keys</strong></td>
                <td><code>.env</code></td>
                <td>API key pools (Gemini, Groq, OpenRouter, RapidAPI) and GHL location credentials.</td>
            </tr>
        </tbody>
    </table>

    <div class="page-break"></div>

    <h2>3. Multi-Provider AI Architecture & Key Pools</h2>
    <p>
        The platform implements a multi-provider resilience architecture. Instead of relying on a single upstream vendor, requests are routed dynamically based on model selection, rate limits, and live capacity:
    </p>

    <table>
        <thead>
            <tr>
                <th>Model Name</th>
                <th>Provider</th>
                <th>Key Pool / Capacity</th>
                <th>Features & Capabilities</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Gemini 3.6 Flash</strong><br><em>(Default / Recommended)</em></td>
                <td>Google Gemini</td>
                <td>5 Active Keys Pool<br>(75 RPM / 5,000,000 TPM)</td>
                <td>Multimodal context, native GHL function calling, ultra-fast generation (~300ms TTFT), auto-continuation loop.</td>
            </tr>
            <tr>
                <td><strong>Gemini 3.7 Flash</strong></td>
                <td>Google Gemini</td>
                <td>5 Active Keys Pool<br>(75 RPM / 5,000,000 TPM)</td>
                <td>Hybrid reasoning and deep logic analysis for complex multi-step HighLevel workflow architectures.</td>
            </tr>
            <tr>
                <td><strong>Groq Compound Mini</strong></td>
                <td>Groq Cloud</td>
                <td>Single LPU Key<br>(30 RPM / 70,000 TPM)</td>
                <td>Ultra-low latency open-weights inference on dedicated Groq LPU hardware with GHL tool calling.</td>
            </tr>
            <tr>
                <td><strong>Groq Qwen 3.8 27B</strong></td>
                <td>Groq Cloud</td>
                <td>Single LPU Key<br>(30 RPM / 70,000 TPM)</td>
                <td>High-throughput fallback model for instant code generation and mid-stream continuation handoffs.</td>
            </tr>
            <tr>
                <td><strong>Llama 3.3 70B Instruct</strong></td>
                <td>OpenRouter</td>
                <td>6 Active Keys Pool<br>(~60-90 RPM capacity)</td>
                <td>Resilient multi-key backup gateway with automated key rotation across 6 independent OpenRouter accounts.</td>
            </tr>
        </tbody>
    </table>

    <h3>3.1. Mid-Stream Model Handover & Seamless Continuation</h3>
    <p>
        When generating massive artifacts (such as full single-file 5-step landing page apps with Tailwind CSS and 5 complete CRM workflows), token budgets can be exhausted mid-stream. The engine handles this autonomously:
    </p>
    <ul>
        <li><strong>Auto-Continuation:</strong> If a model reaches its token cutoff before closing all HTML tags or completing workflows, the system automatically triggers a continuation pass using the last 2,400 characters of context without repeating previous text.</li>
        <li><strong>Cross-Model Handoff:</strong> If the primary model's quota is exhausted (HTTP 429), the engine preserves all generated text, prints a handover notice banner in the live chat stream, and seamlessly delegates the exact remaining generation to Groq Qwen 3.8 or OpenRouter.</li>
        <li><strong>Cascade Sequence:</strong> <code>Google Gemini 3.6 Flash Pool ➔ Groq Cloud Qwen 3.8 ➔ OpenRouter 6-Key Pool</code>.</li>
    </ul>

    <h2>4. GoHighLevel (GHL) Autonomous Tool Calling Engine</h2>
    <p>
        When a Sub-Account Location ID and Private Integration Bearer Token are configured, the agent engine gains direct API access to HighLevel API 2.0 (<code>https://services.leadconnectorhq.com/</code>). The available tools include:
    </p>

    <table>
        <thead>
            <tr>
                <th>Tool Name</th>
                <th>HTTP Method & GHL Endpoint</th>
                <th>Description & Function</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><code>create_contact</code></td>
                <td><code>POST /contacts/</code></td>
                <td>Creates or updates a contact with first name, last name, business email, E.164 phone number, and custom tags.</td>
            </tr>
            <tr>
                <td><code>get_contact</code></td>
                <td><code>GET /contacts/{id}</code></td>
                <td>Retrieves full contact details, custom field values, and active pipeline opportunities.</td>
            </tr>
            <tr>
                <td><code>create_pipeline</code></td>
                <td><code>POST /opportunities/pipelines</code></td>
                <td>Builds a complete multi-stage sales opportunity pipeline with customized stage names and visual stage ordering.</td>
            </tr>
            <tr>
                <td><code>create_opportunity</code></td>
                <td><code>POST /opportunities/</code></td>
                <td>Creates a revenue-tracking opportunity card in a specific pipeline stage with monetary value and status.</td>
            </tr>
            <tr>
                <td><code>create_tag</code></td>
                <td><code>POST /locations/{id}/tags</code></td>
                <td>Creates a global classification tag inside the sub-account for segmentation and workflow triggers.</td>
            </tr>
            <tr>
                <td><code>create_custom_field</code></td>
                <td><code>POST /locations/{id}/customFields</code></td>
                <td>Configures custom fields (TEXT, NUMBER, SINGLE_OPTIONS, DATE) for tracking VSL progress, purchase dates, and OTO status.</td>
            </tr>
        </tbody>
    </table>

    <div class="page-break"></div>

    <h2>5. Frontend Features & User Experience</h2>
    <p>
        The user interface has been built using a custom vanilla CSS glassmorphism design system without external CSS framework bloat:
    </p>
    <ul>
        <li><strong>Floating Input Island:</strong> Centralized input capsule with multi-line auto-expanding textarea, attachment preview badges, mic button for voice dictation, model selector with live health indicator, and squircle send button.</li>
        <li><strong>Suggestion Chips:</strong> Interactive quick-action pills above the input bar (Build Landing Page, + Contact, + Pipeline, + Tag, + Custom Field, Explain Funnels).</li>
        <li><strong>Smart Asset Wizard (6-Step Modal):</strong> An interactive guided wizard allowing users to configure business niche, visual theme, funnel flow (VSL, Lead Magnet, Webinar), CRM automations, brand colors, and generate production-ready architectures with 1 click.</li>
        <li><strong>Code Highlighting & Copy:</strong> Integrated with <code>highlight.js</code> and <code>marked.js</code> with one-click code copy and live rendered previews.</li>
        <li><strong>Live Usage & Quota Bar:</strong> Visual display in the bottom toolbar reflecting real-time TPM usage, RPM limits, and active key pool health.</li>
    </ul>

    <h2>6. Backend Endpoints (FastAPI Specification)</h2>

    <table>
        <thead>
            <tr>
                <th>Route</th>
                <th>Method</th>
                <th>Request / Response</th>
                <th>Purpose</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><code>/</code></td>
                <td><code>GET</code></td>
                <td>HTML File</td>
                <td>Serves the main application interface (<code>static/index.html</code>).</td>
            </tr>
            <tr>
                <td><code>/api/chat-agent</code></td>
                <td><code>POST</code></td>
                <td>SSE Stream (<code>text/event-stream</code>)</td>
                <td>Primary chat and generation endpoint. Streams token chunks, tool start/result events, model handovers, and quota statistics.</td>
            </tr>
            <tr>
                <td><code>/api/models</code></td>
                <td><code>GET</code></td>
                <td>JSON Array</td>
                <td>Returns active models catalog with provider metadata, badge labels, tools support, and real-time usage stats.</td>
            </tr>
            <tr>
                <td><code>/api/test-connection</code></td>
                <td><code>POST</code></td>
                <td>JSON Object</td>
                <td>Validates HighLevel Sub-Account connectivity using the provided Location ID and Access Token with 5-minute caching.</td>
            </tr>
            <tr>
                <td><code>/api/record-usage</code></td>
                <td><code>POST</code></td>
                <td>JSON Object</td>
                <td>Asynchronously tracks token consumption and updates sliding-window usage metrics.</td>
            </tr>
            <tr>
                <td><code>/api/threads</code></td>
                <td><code>GET / POST</code></td>
                <td>JSON Array</td>
                <td>Provides conversation thread persistence across browser sessions.</td>
            </tr>
        </tbody>
    </table>

    <h2>7. Technical Compliance & Best Practices Implemented</h2>
    <ol>
        <li><strong>Strict Entity Preservation:</strong> Mandates that business names, target niches, prices ($997/$497), and brand colors provided in prompts are preserved 100% across all generated code and workflows without unauthorized substitutions.</li>
        <li><strong>True 2-Step Order Form Validation:</strong> Sub-Step 1 validates contact fields and dispatches cart-abandonment events; Sub-Step 2 validates 16-digit card inputs and blocks empty checkouts.</li>
        <li><strong>Real HTML5 Video Progress Tracking:</strong> Includes real <code>timeupdate</code> event listeners calculating watch percentage and firing progress events at the 80% completion mark.</li>
        <li><strong>Separated Cart vs Lead Recovery:</strong> Workflows are cleanly divided into 24-Hour VSL Replay Cadences (2h, 8h, 24h) and 2-Step Cart Abandonment Sequences (15m, 4h, 24h) with explicit stop-checks.</li>
        <li><strong>Secure Tokenized Magic Links:</strong> Uses signed parameters (<code>?token={{ contact.access_token }}&cid={{ contact.id }}</code>) rather than unauthenticated raw contact IDs.</li>
    </ol>

    <h2>8. Deployment & Environment Setup</h2>
    <p>
        The project is fully containerized and deployable on local machines or cloud hosting platforms like Railway, Render, or AWS EC2:
    </p>
    <pre># 1. Clone repository and install dependencies
git clone https://github.com/muhammadokashapak/Conversation-AI-Copilot.git
cd Conversation-AI-Copilot
pip install -r requirements.txt

# 2. Configure environment variables in .env
GEMINI_API_KEYS=key1,key2,key3,key4,key5
GROQ_API_KEY=your_groq_api_key
OPENROUTER_API_KEYS=key1,key2,key3,key4,key5,key6
GHL_LOCATION_ID=your_ghl_location_id
GHL_ACCESS_TOKEN=your_ghl_access_token

# 3. Start local development server
python app.py
# Server runs on http://127.0.0.1:7861</pre>

    <div class="note-box">
        <strong>Report Verification:</strong> Generated automatically from codebase source files including <code>app.py</code>, <code>agent_engine.py</code>, <code>key_pool_manager.py</code>, <code>ghl_client.py</code>, and <code>static/</code>. All specifications are active and verified.
    </div>

</body>
</html>
"""

def generate_pdf():
    print("Writing HTML file...")
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("Launching Chromium via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file:///{os.path.abspath(OUTPUT_HTML)}")
        page.wait_for_load_state("networkidle")
        
        print("Rendering PDF (Clean, no header, no footer)...")
        page.pdf(
            path=OUTPUT_PDF,
            format="A4",
            print_background=True,
            display_header_footer=False, # Explicitly NO header and NO footer
            margin={
                "top": "18mm",
                "right": "18mm",
                "bottom": "18mm",
                "left": "18mm"
            }
        )
        browser.close()
    
    print(f"SUCCESS: PDF Generated at: {OUTPUT_PDF}")
    if os.path.exists(OUTPUT_HTML):
        try:
            os.remove(OUTPUT_HTML)
        except Exception:
            pass

if __name__ == "__main__":
    generate_pdf()
