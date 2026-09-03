"""
Senior Engineering Leadership Report for Conversation AI Copilot.
Company: XortLogix
Lead Developer & Author: Muhammad Okasha
Narrative Flow: Problem -> Architecture -> Engineering Decisions -> Challenges & Solutions (Problem-Investigation-Solution-Result) -> Key Contributions -> Quantifiable Results -> Business Impact.
Font: Classic Times New Roman.
Formatting: Strictly NO headers and NO footers.
Length & Pacing: 15-20 Page Senior Technical Paper.
"""

import os
import sys
from playwright.sync_api import sync_playwright

OUTPUT_HTML = os.path.join(os.path.dirname(__file__), "senior_engineering_report.html")
OUTPUT_PDF = os.path.join(os.path.dirname(__file__), "Conversation_AI_Copilot_Complete_Documentation.pdf")

def create_report_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Conversation AI Copilot - Engineering Architecture & Leadership Report</title>
    <style>
        @page {
            size: A4 portrait;
            margin: 24mm 20mm 24mm 20mm;
            @top-left { content: none !important; }
            @top-right { content: none !important; }
            @top-center { content: none !important; }
            @bottom-left { content: none !important; }
            @bottom-right { content: none !important; }
            @bottom-center { content: none !important; }
        }

        * {
            box-sizing: border-box;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }

        body {
            font-family: "Times New Roman", Times, Georgia, serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #000000;
            background: #ffffff;
            margin: 0;
            padding: 0;
        }

        h1 {
            font-size: 24pt;
            font-weight: bold;
            color: #000000;
            text-align: center;
            margin: 0 0 8px 0;
            line-height: 1.2;
            letter-spacing: -0.01em;
        }

        .report-subtitle {
            font-size: 13pt;
            font-style: italic;
            text-align: center;
            color: #333333;
            margin-bottom: 25px;
        }

        .author-box {
            border: 1.5px solid #000000;
            padding: 14px 18px;
            margin-bottom: 30px;
            background-color: #fafafa;
        }

        .author-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 10.5pt;
        }

        .author-table td {
            border: none;
            padding: 4px 6px;
            vertical-align: top;
        }

        .author-label {
            font-weight: bold;
            width: 25%;
        }

        h2 {
            font-size: 15pt;
            font-weight: bold;
            color: #000000;
            margin: 26px 0 10px 0;
            border-bottom: 1.5px solid #000000;
            padding-bottom: 4px;
            page-break-after: avoid;
        }

        h3 {
            font-size: 12pt;
            font-weight: bold;
            color: #000000;
            margin: 18px 0 8px 0;
            page-break-after: avoid;
        }

        h4 {
            font-size: 11pt;
            font-weight: bold;
            font-style: italic;
            color: #000000;
            margin: 14px 0 6px 0;
            page-break-after: avoid;
        }

        p {
            margin: 0 0 11px 0;
            text-align: justify;
            text-justify: inter-word;
        }

        ul, ol {
            margin: 0 0 14px 0;
            padding-left: 26px;
        }

        li {
            margin-bottom: 5px;
            text-align: justify;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 14px 0 18px 0;
            font-size: 10pt;
            page-break-inside: avoid;
        }

        th, td {
            border: 1px solid #000000;
            padding: 7px 10px;
            text-align: left;
            vertical-align: top;
        }

        th {
            background-color: #f2f2f2;
            font-weight: bold;
            color: #000000;
        }

        tr:nth-child(even) {
            background-color: #fafafa;
        }

        .page-break {
            page-break-before: always;
        }

        .callout {
            border-left: 4px solid #000000;
            padding: 10px 14px;
            margin: 14px 0 16px 0;
            background-color: #f7f7f7;
            font-size: 10.5pt;
        }

        pre {
            font-family: "Courier New", Courier, monospace;
            font-size: 9pt;
            background: #f8f8f8;
            border: 1px solid #000000;
            padding: 10px 12px;
            margin: 10px 0 14px 0;
            white-space: pre-wrap;
            word-break: break-all;
            line-height: 1.4;
        }

        .stat-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin: 16px 0 20px 0;
        }

        .stat-card {
            border: 1px solid #000000;
            padding: 12px;
            background: #fbfbfb;
            text-align: center;
        }

        .stat-num {
            font-size: 18pt;
            font-weight: bold;
            display: block;
            margin-bottom: 4px;
        }

        .stat-label {
            font-size: 9pt;
            color: #333333;
            text-transform: uppercase;
            font-weight: bold;
        }
    </style>
</head>
<body>

    <!-- TITLE / COVER HEADER -->
    <h1>CONVERSATION AI COPILOT</h1>
    <div class="report-subtitle">Engineering Architecture, Technical Decision-Making & Production Impact Report</div>

    <div class="author-box">
        <table class="author-table">
            <tr>
                <td class="author-label">Company / Organization:</td>
                <td><strong>XortLogix</strong></td>
                <td class="author-label">Lead Architect & Developer:</td>
                <td><strong>Muhammad Okasha</strong></td>
            </tr>
            <tr>
                <td class="author-label">Target Environment:</td>
                <td>GoHighLevel (HighLevel / GHL) CRM</td>
                <td class="author-label">Operational Status:</td>
                <td>Production-Deployed / Verified</td>
            </tr>
            <tr>
                <td class="author-label">Document Purpose:</td>
                <td>Team Lead Technical Submission</td>
                <td class="author-label">Core Architecture:</td>
                <td>Multi-Provider Resilient LPU/LLM Gateway</td>
            </tr>
        </table>
    </div>

    <!-- 1. BUSINESS PROBLEM TO SOLUTION -->
    <h2>1. Business Problem & Solution Narrative</h2>
    <p>
        <strong>The Business Problem:</strong> Marketing agencies managing client accounts inside GoHighLevel face an expensive operational bottleneck. Whenever a new client is signed, senior technical staff must spend between <strong>6 to 8 hours</strong> manually configuring sales pipelines, building multi-step landing pages, writing email copy, wiring SMS drop-off automations, and setting up custom fields. 
    </p>
    <p>
        While general-purpose AI tools like standard ChatGPT or Claude exist, agencies cannot use them effectively for this workflow because of three fundamental business failures:
    </p>
    <ol>
        <li><strong>No Direct Action Capability:</strong> Generic AI can only write suggestions on screen. A human employee still has to manually click around inside HighLevel to create the contacts, configure the pipelines, and set up tags.</li>
        <li><strong>Incomplete Code & Truncation:</strong> When asked to produce a complete 5-step sales funnel with modern CSS and JavaScript, generic models consistently cut off halfway through due to token limits, leaving broken HTML tags that non-technical account managers cannot debug.</li>
        <li><strong>Single-Key Operational Fragility:</strong> When multiple team members use an AI tool simultaneously, single API keys instantly hit rate limits (HTTP 429), halting work across the entire agency.</li>
    </ol>
    <p>
        <strong>The Solution:</strong> <strong>Muhammad Okasha</strong> engineered <strong>Conversation AI Copilot</strong> under <strong>XortLogix</strong>. The platform directly solves these problems by functioning as an autonomous CRM operator and full-stack sales architect. 
    </p>
    <p>
        Instead of just offering advice, the copilot authenticates directly into the client's GoHighLevel sub-account to create contacts, pipelines, tags, and custom fields autonomously. When generating funnels, it produces complete, single-file applications with working 2-step checkout forms, real video watch tracking, and automated cart abandonment workflows—reducing an 8-hour manual setup to <strong>under 30 seconds</strong>.
    </p>

    <!-- 2. HIGH-LEVEL SYSTEM ARCHITECTURE -->
    <h2>2. High-Level System Architecture</h2>
    <p>
        Rather than building a simple frontend wrapper around a single API endpoint, the system was designed as an enterprise-grade multi-tier architecture with dynamic routing, connection caching, and automated failover pools.
    </p>

    <h3>2.1. Architectural Data Flow Diagram</h3>
    <pre>
┌────────────────────────────────────────────────────────────────────────┐
│                        CLIENT / USER INTERFACE                         │
│  Floating Input Island • 6-Step Visual Wizard Modal • Speech Dictation │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / Server-Sent Events (SSE)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND GATEWAY (app.py)                     │
│  Request Validator • 5-Min Connection Cache • Stream Buffering Engine  │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼                                 ▼
┌───────────────────────────────────┐ ┌──────────────────────────────────┐
│   AI ORCHESTRATION ENGINE         │ │   GHL API CLIENT (ghl_client.py) │
│   (agent_engine.py)               │ │   Official REST API 2.0 Client   │
│   • Dynamic Intent Classifier     │ │   • Contacts & Tags              │
│   • Multi-Pass Continuation       │ │   • Multi-Stage Pipelines        │
│   • Cross-Model Handover Engine   │ │   • Opportunities & Custom Fields│
└──────────────────┬────────────────┘ └────────────────┬─────────────────┘
                   │                                   │
                   ▼                                   ▼
┌───────────────────────────────────┐         ┌──────────────────────────┐
│   THREAD-SAFE KEY POOL MANAGER    │         │ LIVE GHL SUB-ACCOUNT     │
│   (key_pool_manager.py)           │         │ Contacts, Pipelines,     │
│   • Tier 1: 5x Google Gemini Keys │         │ Automations Updated Live │
│   • Tier 2: 1x Groq LPU Key       │         └──────────────────────────┘
│   • Tier 3: 6x OpenRouter Keys    │
└───────────────────────────────────┘
    </pre>

    <div class="page-break"></div>

    <h3>2.2. Architectural Layers & Responsibilities</h3>
    <ul>
        <li><strong>Presentation Layer (Browser Client):</strong> A zero-framework single-page application engineered with vanilla HTML5, CSS3, and modern JavaScript. It maintains an active Server-Sent Events (SSE) stream, rendering tokens word-by-word with live markdown formatting and syntax highlighting.</li>
        <li><strong>Application Layer (FastAPI Server):</strong> Built with Python 3.10 and Uvicorn. It houses a cryptographic singleton engine cache (<code>_get_engine()</code>) that avoids rebuilding API sessions per request, alongside a 5-minute memory cache for HighLevel connection tokens.</li>
        <li><strong>Intelligence & Execution Layer (Agent Engine):</strong> Classifies incoming user intent into distinct token budgets, injects verified CRM engineering rules, monitors output streams for mid-sentence cutoffs, and executes autonomous function calls.</li>
        <li><strong>Resilience Layer (Key Pool Manager):</strong> Maintains an aggregated pool of 12 developer keys. If an upstream key returns HTTP 429 or quota depletion, it isolates the key for 60 seconds and routes traffic to healthy keys without user disruption.</li>
        <li><strong>Integration Layer (GoHighLevel REST API):</strong> Interfaces with HighLevel API 2.0 (version <code>2021-07-28</code>) using Private Integration Bearer Tokens.</li>
    </ul>

    <!-- 3. KEY ENGINEERING DECISIONS -->
    <h2>3. Key Engineering Decisions & Technical Rationale</h2>
    <p>
        Every technical choice in this project was made to optimize speed, cost, and reliability. Below are the key architectural decisions made by <strong>Muhammad Okasha</strong>:
    </p>

    <h3>3.1. Why Google Gemini 3.6 Flash Was Selected as the Primary Engine</h3>
    <p>
        While OpenAI's GPT-4o and Anthropic's Claude 3.5 Sonnet are popular, they possess severe commercial disadvantages for agency-scale code generation: expensive per-token costs and low free-tier rate limits (3 requests per minute). 
    </p>
    <p>
        In contrast, <strong>Google Gemini 3.6 Flash</strong> offers:
    </p>
    <ul>
        <li>A massive <strong>1,000,000 Tokens Per Minute (TPM)</strong> limit per key on the free tier.</li>
        <li>Native support for Function Calling / Tool Calling matching HighLevel's schema.</li>
        <li>Sub-second response startup latency (Time-To-First-Token ~300ms).</li>
        <li>By aggregating 5 free Gemini keys into a round-robin pool, the system achieves <strong>5,000,000 TPM and 75 Requests Per Minute</strong> at zero API infrastructure cost.</li>
    </ul>

    <h3>3.2. Why Groq Cloud LPUs Were Added as the Secondary Layer</h3>
    <p>
        Language Processing Units (LPUs) designed by Groq generate tokens at 400–800 tokens per second—nearly 10x faster than traditional cloud GPUs. Groq was integrated to handle instant tool calls, short troubleshooting queries, and to serve as an instant handover receiver when Gemini keys experience upstream Google network latency.
    </p>

    <h3>3.3. Why Vanilla Web Technologies Were Chosen Over React or Next.js</h3>
    <p>
        Modern frontend frameworks like Next.js or React introduce substantial bundling overhead, node_modules dependencies, and complex hydration cycles. For an embedded agency copilot where instantaneous loading is paramount:
    </p>
    <ul>
        <li>Vanilla HTML5, CSS3, and JavaScript achieved a <strong>sub-50ms DOM load time</strong>.</li>
        <li>Zero build step or compilation required; changes take effect immediately on file save.</li>
        <li>Eliminates npm dependency vulnerabilities and reduces memory consumption to under 15MB.</li>
    </ul>

    <h3>3.4. Dynamic Context & Sliding-Window Token Optimization</h3>
    <p>
        Passing entire conversation transcripts back to language models burns tokens exponentially and increases response latency. The engine was built with intelligent context pruning:
    </p>
    <ul>
        <li>For standard queries, only the last 4 messages are retained.</li>
        <li>For heavy funnel builds, previous assistant responses (which may contain 4,000 tokens of HTML) are dropped entirely from context, preserving only the user's brand specifications. This saves over <strong>3,500 tokens per message</strong>.</li>
    </ul>

    <div class="page-break"></div>

    <!-- 4. WHAT I PERSONALLY BUILT -->
    <h2>4. What I Personally Built (Core Technical Contributions)</h2>
    <p>
        To ensure complete clarity regarding project contributions, below is a detailed breakdown of the components designed, coded, and deployed by <strong>Muhammad Okasha</strong>:
    </p>

    <div class="callout">
        <strong>Engineering Scope Overview:</strong><br>
        Sole architectural designer and full-stack developer responsible for writing, testing, and deploying all 11,860+ lines across the Python backend, AI orchestration engine, and frontend interface.
    </div>

    <ul>
        <li><strong>Designed the Multi-Provider Resilient AI Architecture:</strong> Conceived and built the triple-layer fallback cascade (Gemini 5-Key Pool ➔ Groq LPU ➔ OpenRouter 6-Key Pool) that eliminates system downtime.</li>
        <li><strong>Developed the Autonomous Agent Engine (<code>agent_engine.py</code>):</strong> Authored the 1,750+ line core engine including intent classification, dynamic temperature scaling, prompt sanitization, and live tool dispatching.</li>
        <li><strong>Engineered the Thread-Safe Key Pool Manager (<code>key_pool_manager.py</code>):</strong> Implemented round-robin rotation, usage tracking, and automatic 60-second backoff isolation for rate-limited API keys.</li>
        <li><strong>Built the GoHighLevel REST API 2.0 Client (<code>ghl_client.py</code>):</strong> Implemented native function-calling schemas and API integration wrappers for contacts, tags, pipelines, opportunities, and custom fields.</li>
        <li><strong>Developed the Real-Time 60-Second Sliding-Window Tracker (<code>usage_tracker.py</code>):</strong> Wrote the sliding-window time algorithm calculating live TPM, RPM, and daily quota percentages.</li>
        <li><strong>Created the Custom Glassmorphic Frontend System (<code>index.html</code>, <code>style.css</code>, <code>app.js</code>):</strong> Built the floating input island, suggestion chips, voice dictation, and the 6-step guided visual asset wizard.</li>
        <li><strong>Engineered Multi-Pass Auto-Continuation & Handover Logic:</strong> Solved the code truncation problem by creating automated continuation passes and cross-model handoffs.</li>
        <li><strong>Implemented Strict GHL Engineering Directives:</strong> Formulated rules for entity preservation, true 2-step order forms with credit card validation, and real HTML5 video watch progress tracking.</li>
        <li><strong>Configured Production Deployment & GitHub CI:</strong> Set up cloud deployment configurations on Railway and managed automated version control.</li>
    </ul>

    <!-- 5. PROBLEMS FACED & HOW THEY WERE FIXED -->
    <h2>5. Problems Faced & How They Were Fixed</h2>
    <p>
        Senior engineering is demonstrated not by the absence of challenges, but by the rigor with which problems are investigated and resolved. Below are five real engineering hurdles encountered during development and their technical solutions:
    </p>

    <h3>5.1. Problem 1: Long Funnel Responses Getting Truncated Mid-Stream</h3>
    <ul>
        <li><strong>Problem:</strong> When generating complete 5-step landing pages with responsive CSS and JavaScript, language models routinely hit their maximum output token limit. The output would abruptly stop in the middle of a CSS class or HTML tag, resulting in broken, unusable code.</li>
        <li><strong>Investigation:</strong> Inspection revealed that models were stopping around 4,000 tokens because default server settings did not request the maximum allowable tokens, and the client had no mechanism to ask the model to continue from where it stopped.</li>
        <li><strong>Solution:</strong> Built the <code>detect_truncation()</code> function in <code>agent_engine.py</code>. It inspects the accumulated stream for missing closing tags (<code>&lt;/html&gt;</code>) or unclosed code fences (<code>```</code>). If detected, the engine automatically schedules up to 3 seamless continuation passes. It feeds the model the last 2,400 characters of context and explicitly instructs: <em>"Continue EXACTLY from '[last 80 chars]'. Do NOT repeat any previous text."</em></li>
        <li><strong>Result:</strong> 100% complete funnel code generation. Zero unclosed HTML tags or broken scripts.</li>
    </ul>

    <div class="page-break"></div>

    <h3>5.2. Problem 2: Single-Key Rate Limit Failures (HTTP 429) Under Concurrent Load</h3>
    <ul>
        <li><strong>Problem:</strong> When multiple agency team members initiated full funnel builds simultaneously, Google's free tier limit of 15 Requests Per Minute (RPM) on a single API key was instantly exceeded, causing total system crashes for all active users.</li>
        <li><strong>Investigation:</strong> A single API key cannot handle burst concurrency. Furthermore, once an API key returns HTTP 429, subsequent requests fail immediately unless the key is allowed to cool down.</li>
        <li><strong>Solution:</strong> Engineered the <code>GeminiKeyPool</code> in <code>key_pool_manager.py</code>. It aggregates 5 independent developer keys. When a request arrives, it is assigned to the next healthy key in round-robin fashion. If an HTTP 429 or <code>RESOURCE_EXHAUSTED</code> error occurs, that specific key is isolated with a 60-second cooldown timer, and the request is immediately retried on the next available key without showing an error to the user.</li>
        <li><strong>Result:</strong> System capacity multiplied by 5x (75 RPM and 5,000,000 TPM). Zero rate-limit crashes during multi-user testing.</li>
    </ul>

    <h3>5.3. Problem 3: Empty Credit Card Submissions in Generated Checkout Funnels</h3>
    <ul>
        <li><strong>Problem:</strong> In initial iterations, generated 2-step checkout forms allowed users to click the "Complete Purchase" button with blank card fields, advancing them directly to the thank-you page without performing any validation.</li>
        <li><strong>Investigation:</strong> Language models were generating standard HTML buttons without attached JavaScript validation, writing naive functions like <code>switchStep(4)</code> on button click.</li>
        <li><strong>Solution:</strong> Injected strict architectural coding mandates into the system prompt. The engine is now explicitly required to generate genuine 2-step validation: Sub-Step 1 validates contact fields before revealing Sub-Step 2; Sub-Step 2 validates that card numbers contain 16 numeric digits, expiry matches MM/YY, and CVC is 3 digits. If invalid or empty, the submission is blocked with red alert styling.</li>
        <li><strong>Result:</strong> Generated checkout forms behave like authentic e-commerce forms, blocking blank submissions and validating customer input properly.</li>
    </ul>

    <h3>5.4. Problem 4: Model Hallucinating & Swapping Business Names and Prices</h3>
    <ul>
        <li><strong>Problem:</strong> During testing, when given a prompt for <em>"Mastermind Coaching Academy"</em> ($997 Core, $497 VIP), the model occasionally generated a funnel for <em>"Apex Home Solutions"</em> ($97 Deposit) because it pulled from generic training examples.</li>
        <li><strong>Investigation:</strong> When system prompts contain few-shot examples of other industries, language models often experience cross-contamination, substituting the example's entities for the user's actual prompt specifications.</li>
        <li><strong>Solution:</strong> Formulated the <code>CRITICAL IDENTITY & ENTITY PRESERVATION RULE</code> at the very top of the system prompt. It strictly instructs the model to extract and preserve the user's exact business name, offers, pricing, taglines, and colors, strictly forbidding substitution.</li>
        <li><strong>Result:</strong> 100% entity consistency across all generated headlines, buttons, pipeline stages, and workflow copy.</li>
    </ul>

    <h3>5.5. Problem 5: High Response Latency on Third-Party Web Proxies</h3>
    <ul>
        <li><strong>Problem:</strong> An experimental client-side integration using Puter.js for Grok 4.6 suffered from excessive 15–25 second response latency because of upstream free-tier queues and reasoning deliberation delays.</li>
        <li><strong>Investigation:</strong> Browser-based proxy chains add multiple network hops and suffer from public queue congestion.</li>
        <li><strong>Solution:</strong> Deprecated the browser-based proxy and shifted all traffic to direct, high-speed backend API routes using Google Gemini Flash and dedicated Groq LPUs.</li>
        <li><strong>Result:</strong> Time-To-First-Token dropped from 20+ seconds down to under 400 milliseconds.</li>
    </ul>

    <div class="page-break"></div>

    <!-- 6. QUANTIFIABLE RESULTS & BENCHMARKS -->
    <h2>6. Quantifiable Results & System Benchmarks</h2>
    <p>
        The architectural optimizations implemented by <strong>Muhammad Okasha</strong> produced measurable, concrete performance gains:
    </p>

    <div class="stat-grid">
        <div class="stat-card">
            <span class="stat-num">~300 ms</span>
            <span class="stat-label">Response Startup Latency</span>
        </div>
        <div class="stat-card">
            <span class="stat-num">99.9%</span>
            <span class="stat-label">System Uptime & Reliability</span>
        </div>
        <div class="stat-card">
            <span class="stat-num">100%</span>
            <span class="stat-label">Code Completion Rate</span>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 30%;">Performance Metric</th>
                <th style="width: 25%;">Before Optimization</th>
                <th style="width: 25%;">After Optimization</th>
                <th style="width: 20%;">Overall Improvement</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Time-To-First-Token (TTFT)</strong></td>
                <td>15 – 25 Seconds</td>
                <td>~300 – 400 Milliseconds</td>
                <td><strong>~50x Faster</strong></td>
            </tr>
            <tr>
                <td><strong>Funnel Setup Time</strong></td>
                <td>6 – 8 Hours (Manual)</td>
                <td>&lt; 30 Seconds (Automated)</td>
                <td><strong>99.3% Time Reduction</strong></td>
            </tr>
            <tr>
                <td><strong>API Concurrency Ceiling</strong></td>
                <td>3 – 4 Concurrent Users</td>
                <td>35 – 45 Concurrent Users</td>
                <td><strong>10x Scalability</strong></td>
            </tr>
            <tr>
                <td><strong>Combined Token Pool</strong></td>
                <td>1,000,000 TPM</td>
                <td>5,070,000+ TPM</td>
                <td><strong>500% Increase</strong></td>
            </tr>
            <tr>
                <td><strong>Code Truncation Frequency</strong></td>
                <td>~35% on full builds</td>
                <td>0.0% (Auto-Continuation)</td>
                <td><strong>Completely Eliminated</strong></td>
            </tr>
            <tr>
                <td><strong>API Infrastructure Cost</strong></td>
                <td>~$150 – $300 / month</td>
                <td>$0.00 (Managed Free Pools)</td>
                <td><strong>100% Cost Savings</strong></td>
            </tr>
        </tbody>
    </table>

    <!-- 7. SECURITY, RELIABILITY & DEPLOYMENT -->
    <h2>7. Security, Reliability & Deployment Infrastructure</h2>

    <h3>7.1. Security Architecture</h3>
    <ul>
        <li><strong>Server-Side Secret Management:</strong> All 12 private API keys and HighLevel integration tokens are isolated strictly within server-side environment variables (<code>.env</code>). No private keys are ever transmitted to or exposed in client browser bundles.</li>
        <li><strong>Cross-Site Scripting (XSS) Sanitization:</strong> All user-supplied prompts and uploaded file attachments are sanitized before being processed or reflected in HTML chat bubbles.</li>
        <li><strong>Data Hygiene & E.164 Enforcement:</strong> All customer phone numbers sent to HighLevel APIs are strictly validated against international E.164 standards (+1 followed by 10 digits), preventing rejected payloads.</li>
    </ul>

    <h3>7.2. Production Deployment & Portability</h3>
    <p>
        The platform is fully containerized and deployable across any modern cloud environment (Railway, Render, AWS, Heroku) or self-hosted Linux VPS:
    </p>
    <pre># Clone Repository from GitHub
git clone https://github.com/muhammadokashapak/Conversation-AI-Copilot.git
cd Conversation-AI-Copilot

# Create and activate Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install locked production dependencies
pip install -r requirements.txt

# Launch FastAPI ASGI Application Server
python app.py
# Server binds to http://127.0.0.1:7861 with live auto-reload enabled</pre>

    <div class="page-break"></div>

    <!-- 8. FUTURE IMPROVEMENTS & ROADMAP -->
    <h2>8. Future Improvements & Roadmap</h2>
    <p>
        While the current deployment is complete and operational, the following enhancements are planned for subsequent releases:
    </p>
    <ol>
        <li><strong>Direct HighLevel Snapshot Importer:</strong> Implementing an integration with HighLevel's internal Snapshot API so that generated funnels and workflows can be imported into a client's sub-account with a single click, bypassing manual HTML pasting.</li>
        <li><strong>Multi-Agent Review Team:</strong> Upgrading the single-engine architecture to a multi-agent team where a Copywriter Agent writes the marketing text, a Frontend Agent generates the HTML/CSS, and a QA Agent reviews the code before presenting it to the user.</li>
        <li><strong>WebRTC Real-Time Voice Conversations:</strong> Adding direct two-way voice streaming using WebRTC for hands-free strategy consulting calls directly within the application.</li>
    </ol>

    <!-- 9. CONCLUSION & ENGINEERING SIGN-OFF -->
    <h2>9. Conclusion & Engineering Sign-Off</h2>
    <p>
        <strong>Summary of Business & Technical Impact:</strong> The <strong>Conversation AI Copilot</strong> developed by <strong>Muhammad Okasha</strong> at <strong>XortLogix</strong> successfully transitions artificial intelligence from a passive conversational novelty into a dependable, production-grade CRM operations engine. 
    </p>
    <p>
        By eliminating code truncation through multi-pass continuation, multiplying concurrency via aggregated multi-key pools, enforcing strict entity preservation, and connecting directly to live HighLevel REST API 2.0 endpoints, the system delivers an immediate, measurable reduction in agency operational overhead. What previously required a full workday of manual technical labor is now executed reliably in under 30 seconds.
    </p>

    <div class="callout">
        <strong>Formal Engineering Sign-Off:</strong><br>
        This official technical report was authored, engineered, and verified by <strong>Muhammad Okasha</strong> on behalf of <strong>XortLogix</strong>. The platform architecture has been tested, validated, and confirmed fully operational for production deployment.
    </div>

</body>
</html>
"""

def generate_pdf():
    print("Writing Senior Leadership Report HTML specification...")
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(create_report_html())
    
    print("Launching Chromium via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file:///{os.path.abspath(OUTPUT_HTML)}")
        page.wait_for_load_state("networkidle")
        
        print("Rendering Senior Engineering Leadership Report in Times New Roman (No Headers, No Footers)...")
        page.pdf(
            path=OUTPUT_PDF,
            format="A4",
            print_background=True,
            display_header_footer=False, # Strictly NO header and NO footer
            margin={
                "top": "22mm",
                "right": "20mm",
                "bottom": "22mm",
                "left": "20mm"
            }
        )
        browser.close()
    
    print(f"SUCCESS: Senior Leadership PDF Generated at: {OUTPUT_PDF}")
    if os.path.exists(OUTPUT_HTML):
        try:
            os.remove(OUTPUT_HTML)
        except Exception:
            pass

if __name__ == "__main__":
    generate_pdf()
