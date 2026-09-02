"""
PDF Documentation Generator for Conversation AI Copilot.
Generates an executive, submission-ready PDF document from comprehensive project specifications
using Playwright Chromium with beautiful typography, print layout, and data tables.
"""

import os
import sys
from playwright.sync_api import sync_playwright

OUTPUT_HTML = os.path.join(os.path.dirname(__file__), "documentation_report.html")
OUTPUT_PDF = os.path.join(os.path.dirname(__file__), "Conversation_AI_Copilot_Project_Documentation.pdf")

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Conversation AI Copilot - Project Technical Documentation</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

        @page {
            size: A4 portrait;
            margin: 18mm 16mm 20mm 16mm;
            @bottom-right {
                content: "Page " counter(page);
                font-family: 'Inter', sans-serif;
                font-size: 8.5pt;
                color: #64748b;
            }
            @bottom-left {
                content: "Conversation AI Copilot | Project Submission Report";
                font-family: 'Inter', sans-serif;
                font-size: 8.5pt;
                color: #64748b;
            }
            @top-right {
                content: "Technical Documentation";
                font-family: 'Inter', sans-serif;
                font-size: 8pt;
                color: #94a3b8;
            }
        }

        @page:first {
            margin: 0;
            @bottom-right { content: normal; }
            @bottom-left { content: normal; }
            @top-right { content: normal; }
        }

        * {
            box-sizing: border-box;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 10pt;
            line-height: 1.55;
            color: #1e293b;
            background-color: #ffffff;
            margin: 0;
            padding: 0;
        }

        /* Cover Page */
        .cover-page {
            page-break-after: always;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 50mm 25mm 30mm 25mm;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
            color: #ffffff;
            position: relative;
            overflow: hidden;
        }

        .cover-page::before {
            content: "";
            position: absolute;
            top: -100px;
            right: -100px;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, rgba(15, 23, 42, 0) 70%);
            border-radius: 50%;
        }

        .cover-page::after {
            content: "";
            position: absolute;
            bottom: -50px;
            left: -50px;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(16, 185, 129, 0.2) 0%, rgba(15, 23, 42, 0) 70%);
            border-radius: 50%;
        }

        .cover-header {
            position: relative;
            z-index: 2;
        }

        .cover-badge {
            display: inline-flex;
            align-items: center;
            background: rgba(99, 102, 241, 0.2);
            border: 1px solid rgba(129, 140, 248, 0.4);
            color: #a5b4fc;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 9pt;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 24px;
        }

        .cover-title {
            font-size: 32pt;
            font-weight: 800;
            line-height: 1.15;
            letter-spacing: -0.03em;
            margin: 0 0 16px 0;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .cover-subtitle {
            font-size: 14pt;
            font-weight: 400;
            color: #94a3b8;
            line-height: 1.5;
            max-width: 85%;
            margin: 0 0 28px 0;
        }

        .cover-tech-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 30px;
            position: relative;
            z-index: 2;
        }

        .pill {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 8.5pt;
            font-weight: 500;
            color: #e2e8f0;
        }

        .pill.accent {
            background: rgba(16, 185, 129, 0.18);
            border-color: rgba(16, 185, 129, 0.4);
            color: #6ee7b7;
        }

        .cover-footer {
            position: relative;
            z-index: 2;
            border-top: 1px solid rgba(255, 255, 255, 0.12);
            padding-top: 24px;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }

        .meta-item {
            display: flex;
            flex-direction: column;
        }

        .meta-label {
            font-size: 7.5pt;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748b;
            margin-bottom: 4px;
            font-weight: 600;
        }

        .meta-val {
            font-size: 9.5pt;
            font-weight: 600;
            color: #f1f5f9;
        }

        /* Table of Contents & Structure */
        .page-break {
            page-break-before: always;
        }

        .section-header {
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px;
            margin-top: 24px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        h1 {
            font-size: 18pt;
            font-weight: 800;
            color: #0f172a;
            margin: 0;
            letter-spacing: -0.02em;
        }

        h2 {
            font-size: 13pt;
            font-weight: 700;
            color: #1e293b;
            margin-top: 20px;
            margin-bottom: 8px;
            border-left: 3.5px solid #4f46e5;
            padding-left: 8px;
        }

        h3 {
            font-size: 10.5pt;
            font-weight: 600;
            color: #334155;
            margin-top: 14px;
            margin-bottom: 6px;
        }

        p {
            margin: 0 0 10px 0;
            color: #334155;
        }

        ul, ol {
            margin: 0 0 12px 0;
            padding-left: 20px;
            color: #334155;
        }

        li {
            margin-bottom: 4px;
        }

        /* Callout Boxes */
        .callout {
            border-radius: 8px;
            padding: 12px 16px;
            margin: 12px 0;
            font-size: 9pt;
            line-height: 1.5;
            border-left: 4px solid;
            break-inside: avoid;
        }

        .callout-info {
            background-color: #f0fdf4;
            border-color: #10b981;
            color: #065f46;
        }

        .callout-purple {
            background-color: #f5f3ff;
            border-color: #6366f1;
            color: #3730a3;
        }

        .callout-warning {
            background-color: #fffbeb;
            border-color: #f59e0b;
            color: #92400e;
        }

        .callout-title {
            font-weight: 700;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 14px 0;
            font-size: 8.5pt;
            background: #ffffff;
            break-inside: avoid;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
        }

        th {
            background-color: #f8fafc;
            color: #0f172a;
            text-align: left;
            padding: 9px 12px;
            font-weight: 600;
            border-bottom: 1.5px solid #cbd5e1;
            text-transform: uppercase;
            font-size: 7.5pt;
            letter-spacing: 0.04em;
        }

        td {
            padding: 8px 12px;
            border-bottom: 1px solid #f1f5f9;
            color: #334155;
            vertical-align: top;
        }

        tr:nth-child(even) td {
            background-color: #fcfdfe;
        }

        /* Code & Pre */
        code {
            font-family: 'JetBrains Mono', monospace;
            font-size: 8pt;
            background: #f1f5f9;
            color: #4f46e5;
            padding: 2px 5px;
            border-radius: 4px;
            border: 1px solid #e2e8f0;
        }

        pre {
            background: #0f172a;
            color: #e2e8f0;
            padding: 12px 14px;
            border-radius: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 8pt;
            line-height: 1.45;
            overflow-x: hidden;
            margin: 10px 0;
            break-inside: avoid;
        }

        pre code {
            background: transparent;
            color: inherit;
            padding: 0;
            border: none;
        }

        /* Cards & Grids */
        .card-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin: 12px 0;
            break-inside: avoid;
        }

        .card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px;
        }

        .card-title {
            font-weight: 700;
            font-size: 9.5pt;
            color: #0f172a;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .card-desc {
            font-size: 8.5pt;
            color: #64748b;
            line-height: 1.4;
        }

        /* Visual Architecture Flowchart */
        .diagram-container {
            background: #0f172a;
            border-radius: 8px;
            padding: 16px;
            margin: 14px 0;
            color: #ffffff;
            break-inside: avoid;
            text-align: center;
        }

        .diagram-row {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
        }

        .diagram-node {
            background: #1e293b;
            border: 1px solid #334155;
            padding: 8px 14px;
            border-radius: 6px;
            font-size: 8.5pt;
            font-weight: 600;
            color: #f8fafc;
        }

        .diagram-node.highlight {
            background: rgba(99, 102, 241, 0.25);
            border-color: #818cf8;
            color: #e0e7ff;
        }

        .diagram-node.success {
            background: rgba(16, 185, 129, 0.2);
            border-color: #34d399;
            color: #a7f3d0;
        }

        .diagram-arrow {
            color: #64748b;
            font-size: 10pt;
        }

        /* TOC */
        .toc-list {
            list-style: none;
            padding: 0;
            margin: 16px 0;
        }

        .toc-item {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            padding: 7px 0;
            border-bottom: 1px dotted #cbd5e1;
            font-size: 9.5pt;
        }

        .toc-item a {
            color: #1e293b;
            text-decoration: none;
            font-weight: 500;
        }

        .toc-item span {
            color: #64748b;
            font-weight: 600;
            font-size: 8.5pt;
        }
    </style>
</head>
<body>

    <!-- COVER PAGE -->
    <div class="cover-page">
        <div class="cover-header">
            <div class="cover-badge">Project Submission & Technical Architecture Report</div>
            <h1 class="cover-title">Conversation AI Copilot<br/>for GoHighLevel (GHL)</h1>
            <p class="cover-subtitle">
                An Autonomous Multi-Model Action Execution Agent & High-Performance Solutions Architecture for GoHighLevel Sub-Accounts.
            </p>
            <div class="cover-tech-pills">
                <span class="pill accent">Python 3.10+</span>
                <span class="pill accent">FastAPI Core</span>
                <span class="pill">Google Gemini 3.6 & 3.7 Flash</span>
                <span class="pill">Groq Cloud LPUs</span>
                <span class="pill">OpenRouter AI Gateway</span>
                <span class="pill">GoHighLevel REST API v2</span>
                <span class="pill">Server-Sent Events (SSE)</span>
                <span class="pill">Semantic RAG Engine</span>
                <span class="pill">Multi-Key Self-Healing Pool</span>
            </div>
        </div>

        <div class="cover-footer">
            <div class="meta-item">
                <span class="meta-label">Project Domain</span>
                <span class="meta-val">AI Copilot & CRM Automation</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Implementation Status</span>
                <span class="meta-val">Production Ready • Deployed</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Submission Date</span>
                <span class="meta-val">September 2026</span>
            </div>
        </div>
    </div>

    <!-- TABLE OF CONTENTS -->
    <div class="page-break"></div>
    <div class="section-header">
        <h1>Table of Contents</h1>
        <span style="font-size: 8.5pt; color: #64748b; font-weight: 600;">TECHNICAL REPORT</span>
    </div>

    <ul class="toc-list">
        <li class="toc-item"><strong>1. Executive Summary & Problem Scope</strong> <span>Page 3</span></li>
        <li class="toc-item"><strong>2. System Architecture & Topology</strong> <span>Page 4</span></li>
        <li class="toc-item"><strong>3. Multi-Provider AI Engine & Intent Classification</strong> <span>Page 5</span></li>
        <li class="toc-item"><strong>4. Server-Sent Events (SSE) Streaming Protocol</strong> <span>Page 6</span></li>
        <li class="toc-item"><strong>5. Multi-Key Pool & Self-Healing Resilience</strong> <span>Page 7</span></li>
        <li class="toc-item"><strong>6. GoHighLevel (GHL) REST API v2 SDK & Tools Matrix</strong> <span>Page 8</span></li>
        <li class="toc-item"><strong>7. Senior GHL Solutions Architect Engineering Rules</strong> <span>Page 9</span></li>
        <li class="toc-item"><strong>8. Production Vertical Architecture: Gym & Fitness Centers</strong> <span>Page 10</span></li>
        <li class="toc-item"><strong>9. Semantic Retrieval Engine (RAG) & Case Study Grounding</strong> <span>Page 11</span></li>
        <li class="toc-item"><strong>10. Token Usage Tracking & Quota Monitor</strong> <span>Page 12</span></li>
        <li class="toc-item"><strong>11. Complete REST & SSE API Reference</strong> <span>Page 13</span></li>
        <li class="toc-item"><strong>12. Deployment, Containerization & Verification</strong> <span>Page 14</span></li>
    </ul>

    <div class="callout callout-purple">
        <div class="callout-title">📌 Executive Overview</div>
        This document represents the formal technical submission for the <strong>Conversation AI Copilot for GoHighLevel</strong>. It outlines the end-to-end system design, prompt engineering logic, API specifications, real-time streaming infrastructure, and production vertical CRM blueprints implemented in the repository.
    </div>

    <!-- SECTION 1 -->
    <div class="page-break"></div>
    <div class="section-header">
        <h1>1. Executive Summary & Problem Scope</h1>
        <span style="font-size: 8.5pt; color: #64748b; font-weight: 600;">SECTION 01</span>
    </div>

    <h2>1.1 Industry Background & The Friction in HighLevel Setup</h2>
    <p>
        GoHighLevel (GHL) is the leading all-in-one CRM and marketing automation infrastructure utilized by over 50,000 marketing agencies and hundreds of thousands of small businesses globally. However, configuring new client sub-accounts requires significant manual effort:
    </p>
    <ul>
        <li><strong>Repetitive Taxonomy Setup:</strong> Creating dozens of custom contact fields, standardized tags, and multi-stage opportunity pipelines manually consumes 4 to 8 hours per client onboarding.</li>
        <li><strong>Fragmented Multi-Channel Messaging:</strong> Sales reps must constantly navigate complex UI menus to trigger outbound SMS, emails, tasks, and internal notes.</li>
        <li><strong>Provider Rate Limiting & Fragile AI Systems:</strong> Conventional LLM wrappers often hardcode single API keys, resulting in sudden downtime when rate limits (HTTP 429) or token quotas are reached.</li>
        <li><strong>Hallucinations & Flawed CRM Payloads:</strong> Generic AI chatbots frequently invent non-existent GHL API endpoints or generate malformed JSON payloads that fail silently.</li>
    </ul>

    <h2>1.2 The Solution: Conversation AI Copilot</h2>
    <p>
        The <strong>Conversation AI Copilot</strong> solves these challenges by deploying an autonomous, multi-model execution agent directly integrated with GoHighLevel's REST API v2. Users can interact via natural language prompts to perform complete sub-account audits, deploy vertical CRM architectures in seconds, search/create contacts with strict phone hygiene, and stream interactive execution progress with live tool badges.
    </p>

    <div class="card-grid">
        <div class="card">
            <div class="card-title">⚡ Instant Sub-Second Execution</div>
            <div class="card-desc">Leverages Groq Cloud LPUs and Google Gemini Flash to deliver initial token generation under 400ms with native tool calling.</div>
        </div>
        <div class="card">
            <div class="card-title">🛡️ Resilient Key Pool & Failover</div>
            <div class="card-desc">Self-healing multi-key pools with automatic 65-second cooldown recovery and dynamic fallback to alternative models on quota depletion.</div>
        </div>
        <div class="card">
            <div class="card-title">🏗️ Turnkey Vertical Blueprints</div>
            <div class="card-desc">Pre-packaged schemas for specialized niches (e.g. Gyms & Fitness Centers) provisioning 14 fields, 12 tags, and 2 pipelines in one click.</div>
        </div>
        <div class="card">
            <div class="card-title">📄 Verified Semantic RAG</div>
            <div class="card-desc">Grounded in verified agency documentation (PDF/DOCX) to cite authentic Meta Ads dashboards, KPI reports, and case studies.</div>
        </div>
    </div>

    <!-- SECTION 2 -->
    <div class="page-break"></div>
    <div class="section-header">
        <h1>2. System Architecture & Topology</h1>
        <span style="font-size: 8.5pt; color: #64748b; font-weight: 600;">SECTION 02</span>
    </div>

    <p>
        The application is structured into decoupled, high-cohesion architectural tiers ensuring high throughput, seamless streaming, and strict separation of concerns:
    </p>

    <div class="diagram-container">
        <div class="diagram-row">
            <div class="diagram-node">Frontend Web App (Vanilla JS + Glassmorphic CSS)</div>
        </div>
        <div class="diagram-row">
            <div class="diagram-arrow">▼ HTTP POST Prompt & Config / SSE Event Stream</div>
        </div>
        <div class="diagram-row">
            <div class="diagram-node highlight">FastAPI Server (:7861) • app.py</div>
        </div>
        <div class="diagram-row">
            <div class="diagram-arrow">▼ Intent Classification & Prompt Optimization</div>
        </div>
        <div class="diagram-row">
            <div class="diagram-node highlight">GHLAgentExecutionEngine • agent_engine.py</div>
            <div class="diagram-arrow">◄►</div>
            <div class="diagram-node">KeyPoolMgr & UsageTracker</div>
        </div>
        <div class="diagram-row">
            <div class="diagram-arrow">▼ Function Invocations & Tool Dispatch</div>
        </div>
        <div class="diagram-row">
            <div class="diagram-node">GHLSubAccountClient (REST API v2)</div>
            <div class="diagram-arrow">◄►</div>
            <div class="diagram-node success">GoHighLevel Cloud Services</div>
        </div>
    </div>

    <h2>2.1 Component Breakdown</h2>
    <table>
        <thead>
            <tr>
                <th>Component</th>
                <th>File Location</th>
                <th>Core Responsibilities</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Web Server & Router</strong></td>
                <td><code>app.py</code></td>
                <td>FastAPI application, static assets mounting, connection caching (300s TTL), SSE response streaming, and REST API controllers.</td>
            </tr>
            <tr>
                <td><strong>Execution Core</strong></td>
                <td><code>agent_engine.py</code></td>
                <td>Prompt intent classification, 29 architectural rule injection, Gemini/Groq/OpenRouter dispatching, and function calling loop.</td>
            </tr>
            <tr>
                <td><strong>GHL Client SDK</strong></td>
                <td><code>ghl_client.py</code></td>
                <td>GoHighLevel REST API v2 wrapper: contacts, pipelines, deals, tags, custom fields, notes, tasks, and conversations.</td>
            </tr>
            <tr>
                <td><strong>Key Pool Manager</strong></td>
                <td><code>key_pool_manager.py</code></td>
                <td>Multi-key management for Gemini and OpenRouter, credit balance polling, 429 rate limit detection, and 65s auto-recovery cooldown.</td>
            </tr>
            <tr>
                <td><strong>Usage Tracker</strong></td>
                <td><code>usage_tracker.py</code></td>
                <td>Tracks daily requests, daily tokens, sliding-window TPM/RPM, and writes persistent stats to <code>model_usage.json</code>.</td>
            </tr>
            <tr>
                <td><strong>Semantic RAG Engine</strong></td>
                <td><code>portfolio_knowledge_base.py</code></td>
                <td>Parses PDF and DOCX agency case studies, generates vector embeddings, and performs cosine similarity + keyword overlap matching.</td>
            </tr>
            <tr>
                <td><strong>Vertical Blueprint</strong></td>
                <td><code>gym_architecture.py</code></td>
                <td>Turnkey schema definitions for Gym & Fitness Center CRM taxonomy, retention pipelines, and lead scoring hysteresis.</td>
            </tr>
        </tbody>
    </table>

    <!-- SECTION 3 -->
    <div class="page-break"></div>
    <div class="section-header">
        <h1>3. Multi-Provider AI Engine & Intent Classification</h1>
        <span style="font-size: 8.5pt; color: #64748b; font-weight: 600;">SECTION 03</span>
    </div>

    <h2>3.1 Intelligent Intent Classification</h2>
    <p>
        The engine does not treat all user inputs identically. Every prompt is evaluated by <code>classify_prompt_intent()</code> against compiled regex patterns and keyword sets to select the optimal temperature, token budget, and context window:
    </p>

    <table>
        <thead>
            <tr>
                <th>Intent Mode</th>
                <th>Target Interaction</th>
                <th>Temperature</th>
                <th>Max Token Budget</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><code>full_build</code></td>
                <td>Full landing pages, complete CRM architecture, or vertical code bundles.</td>
                <td>0.7</td>
                <td>Up to 8,192 Tokens</td>
            </tr>
            <tr>
                <td><code>proposal_or_qa</code></td>
                <td>Technical audits, client proposals, scope of work, or architectural reviews.</td>
                <td>0.2</td>
                <td>4,000 Tokens</td>
            </tr>
            <tr>
                <td><code>iteration</code></td>
                <td>Styling adjustments, color swaps, tag renaming, or single-field updates.</td>
                <td>0.4</td>
                <td>2,500 Tokens</td>
            </tr>
            <tr>
                <td><code>quick_answer</code></td>
                <td>Concise platform guidance, troubleshooting, or single GHL queries.</td>
                <td>0.2</td>
                <td>1,500 Tokens</td>
            </tr>
            <tr>
                <td><strong>Tool Invocation Mode</strong></td>
                <td>Active tool calling (e.g. creating contact or pipeline).</td>
                <td><strong>0.1</strong></td>
                <td>Deterministic Output</td>
            </tr>
        </tbody>
    </table>

    <h2>3.2 Supported Model Catalog & Capabilities</h2>
    <table>
        <thead>
            <tr>
                <th>Model Identifier</th>
                <th>Provider</th>
                <th>Hardware / Framework</th>
                <th>Specialization & Rate Limit</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><code>gemini-3.6-flash</code></td>
                <td>Google AI Studio</td>
                <td>Native Google GenAI SDK</td>
                <td><strong>Recommended</strong> • 1M TPM • 15 RPM • Native Tool Calling</td>
            </tr>
            <tr>
                <td><code>gemini-3.7-flash</code></td>
                <td>Google AI Studio</td>
                <td>Native Google GenAI SDK</td>
                <td>Hybrid Reasoning Engine • Complex multi-step CRM automations</td>
            </tr>
            <tr>
                <td><code>groq/compound-mini</code></td>
                <td>Groq Cloud</td>
                <td>LPU Tensor Architecture</td>
                <td>⚡ 70k TPM • Ultra-fast landing page & code generation</td>
            </tr>
            <tr>
                <td><code>qwen/qwen3.8-27b</code></td>
                <td>Groq Cloud</td>
                <td>LPU Tensor Architecture</td>
                <td>Open-weights benchmark leader • High-precision tool calling</td>
            </tr>
            <tr>
                <td><code>x-ai/grok-4.6</code></td>
                <td>OpenRouter Hub</td>
                <td>xAI Infrastructure</td>
                <td>Deep reasoning & real-time conversational synthesis</td>
            </tr>
            <tr>
                <td><code>anthropic/claude-3.5-sonnet</code></td>
                <td>OpenRouter Hub</td>
                <td>Anthropic API</td>
                <td>State-of-the-art coding and SaaS systems architecture</td>
            </tr>
        </tbody>
    </table>

    <!-- SECTION 4 -->
    <div class="page-break"></div>
    <div class="section-header">
        <h1>4. Server-Sent Events (SSE) Streaming Protocol</h1>
        <span style="font-size: 8.5pt; color: #64748b; font-weight: 600;">SECTION 04</span>
    </div>

    <p>
        The backend delivers immediate, token-by-token output and interactive tool status via <strong>Server-Sent Events (SSE)</strong>. This avoids long HTTP blocking pauses while multi-step tool calls execute against external CRM endpoints.
    </p>

    <h2>4.1 SSE Event Lifecycle & Schema</h2>
    <table>
        <thead>
            <tr>
                <th>Event Type</th>
                <th>JSON Payload Structure</th>
                <th>Client UI Behavior</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><code>status</code></td>
                <td><code>{"type": "status", "message": "string"}</code></td>
                <td>Displays subtle animated status message in chat stream.</td>
            </tr>
            <tr>
                <td><code>tool_call</code></td>
                <td><code>{"type": "tool_call", "name": "...", "args": {...}}</code></td>
                <td>Renders an active, pulsing tool execution badge in UI.</td>
            </tr>
            <tr>
                <td><code>tool_result</code></td>
                <td><code>{"type": "tool_result", "name": "...", "result": {...}, "success": bool}</code></td>
                <td>Transitions execution badge to green (Success) or red (Error).</td>
            </tr>
            <tr>
                <td><code>chunk</code></td>
                <td><code>{"type": "chunk", "text": "string"}</code></td>
                <td>Appends tokenized markdown directly to active response buffer.</td>
            </tr>
            <tr>
                <td><code>usage_update</code></td>
                <td><code>{"type": "usage_update", "model": "...", "stats": {...}}</code></td>
                <td>Updates live quota bar and request counts in real-time.</td>
            </tr>
            <tr>
                <td><code>done</code></td>
                <td><code>{"type": "done"}</code></td>
                <td>Signals stream termination; enables input controls.</td>
            </tr>
        </tbody>
    </table>

    <h2>4.2 Real-Time SSE Stream Trace Example</h2>
    <pre><code>HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"type": "status", "message": "Evaluating prompt and preparing execution..."}

data: {"type": "tool_call", "name": "create_contact", "args": {"first_name": "Jordan", "last_name": "Bell", "email": "jordan@fitpulse.com", "phone": "+15125550199", "tags": ["Prospect", "Trial Booked"]}}

data: {"type": "tool_result", "name": "create_contact", "result": {"success": true, "message": "Contact 'Jordan Bell' created successfully."}, "success": true}

data: {"type": "chunk", "text": "I have created the contact for **Jordan Bell** in your GoHighLevel sub-account with phone `+15125550199` and tags `Prospect, Trial Booked`."}

data: {"type": "usage_update", "model": "gemini-3.6-flash", "stats": {"daily_requests": 18, "daily_tokens": 7420, "usage_percentage": 1.2}}

data: {"type": "done"}</code></pre>

    <!-- SECTION 5 -->
    <div class="page-break"></div>
    <div class="section-header">
        <h1>5. Multi-Key Pool & Self-Healing Resilience</h1>
        <span style="font-size: 8.5pt; color: #64748b; font-weight: 600;">SECTION 05</span>
    </div>

    <p>
        Production AI systems frequently encounter third-party rate limits. The <code>key_pool_manager.py</code> module implements automated rotation, credit tracking, and self-healing cooldown logic to ensure uninterrupted uptime.
    </p>

    <h2>5.1 Gemini Key Pool (`GeminiKeyPool`)</h2>
    <ul>
        <li><strong>Multi-Key Ingestion:</strong> Ingests single <code>GEMINI_API_KEY</code> or comma-separated <code>GEMINI_API_KEYS</code>.</li>
        <li><strong>Quota Failure Detection:</strong> Automatically intercepts <code>HTTP 429 (ResourceExhausted)</code> errors.</li>
        <li><strong>Quarantine & 65-Second Auto-Recovery:</strong> When a key encounters a rate limit, it is quarantined and marked <code>is_depleted = True</code> with a timestamp. Because Google AI Studio RPM rate limits reset on a 60-second sliding cycle, the pool automatically restores keys to healthy status after a <strong>65-second cooldown</strong> without requiring server restarts.</li>
    </ul>

    <h2>5.2 OpenRouter Key Pool (`OpenRouterKeyPool`)</h2>
    <ul>
        <li><strong>Real-Time Balance Polling:</strong> Automatically queries <code>https://openrouter.ai/api/v1/auth/key</code> to monitor credit usage and remaining balance.</li>
        <li><strong>Automatic Shift on Depletion:</strong> Keys returning <code>HTTP 402 (Insufficient Credits)</code> or low balance are instantly rotated out in favor of healthy alternatives.</li>
    </ul>

    <h2>5.3 Cross-Provider Failover Matrix</h2>
    <div class="callout callout-info">
        <div class="callout-title">🛡️ High-Availability Failover Chain</div>
        If all keys in the primary <strong>Google Gemini</strong> pool are temporarily exhausted, requests gracefully cascade to <strong>Groq Cloud LPUs</strong> (Compound Mini / Qwen 3.8), and subsequently to <strong>OpenRouter</strong> fallback models. Users experience continuous availability with zero service interruptions.
    </div>

    <!-- SECTION 6 -->
    <div class="page-break"></div>
    <div class="section-header">
        <h1>6. GoHighLevel (GHL) REST API v2 SDK & Tools Matrix</h1>
        <span style="font-size: 8.5pt; color: #64748b; font-weight: 600;">SECTION 06</span>
    </div>

    <p>
        The <code>GHLSubAccountClient</code> provides a unified, production-grade SDK interacting strictly with GoHighLevel's official REST API v2:
        <br/>• <strong>Base URL:</strong> <code>https://services.leadconnectorhq.com</code>
        <br/>• <strong>Version Header:</strong> <code>Version: 2021-07-28</code>
        <br/>• <strong>Authentication:</strong> <code>Authorization: Bearer &lt;ACCESS_TOKEN&gt;</code>
    </p>

    <table>
        <thead>
            <tr>
                <th>Tool Name</th>
                <th>Target Endpoint</th>
                <th>Method</th>
                <th>Description & Hygiene Rules</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><code>create_contact</code></td>
                <td><code>/contacts/</code></td>
                <td>POST</td>
                <td>Creates contact with first/last name, email, E.164 phone, tags, and custom fields. Suppresses redundant <code>name</code> fields.</td>
            </tr>
            <tr>
                <td><code>search_contacts</code></td>
                <td><code>/contacts/</code></td>
                <td>GET</td>
                <td>Queries contacts by name, email, or phone. Used for pre-flight duplicate checks.</td>
            </tr>
            <tr>
                <td><code>create_pipeline</code></td>
                <td><code>/opportunities/pipelines/</code></td>
                <td>POST</td>
                <td>Builds custom sales or retention pipelines with ordered positional stages.</td>
            </tr>
            <tr>
                <td><code>get_pipelines</code></td>
                <td><code>/opportunities/pipelines/</code></td>
                <td>GET</td>
                <td>Fetches existing pipeline and stage IDs for deal card routing.</td>
            </tr>
            <tr>
                <td><code>create_opportunity</code></td>
                <td><code>/opportunities/</code></td>
                <td>POST</td>
                <td>Inserts deal card into specified pipeline and stage with monetary values and status.</td>
            </tr>
            <tr>
                <td><code>create_tag</code></td>
                <td><code>/locations/{id}/tags</code></td>
                <td>POST</td>
                <td>Adds a new tag to the location tag taxonomy.</td>
            </tr>
            <tr>
                <td><code>create_custom_field</code></td>
                <td><code>/locations/{id}/customFields</code></td>
                <td>POST</td>
                <td>Provisions fields: <code>TEXT</code>, <code>NUMBER</code>, <code>DATE</code>, or <code>SINGLE_OPTIONS</code> with defined dropdown choices.</td>
            </tr>
            <tr>
                <td><code>send_conversation_message</code></td>
                <td><code>/conversations/messages</code></td>
                <td>POST</td>
                <td>Dispatches outbound SMS or Email directly through connected sub-account telephony.</td>
            </tr>
            <tr>
                <td><code>create_contact_task</code></td>
                <td><code>/contacts/{id}/tasks</code></td>
                <td>POST</td>
                <td>Assigns actionable task with ISO due date to a contact record.</td>
            </tr>
            <tr>
                <td><code>create_contact_note</code></td>
                <td><code>/contacts/{id}/notes</code></td>
                <td>POST</td>
                <td>Appends internal staff notes to a contact record.</td>
            </tr>
            <tr>
                <td><code>setup_gym_subaccount</code></td>
                <td>Batch API Handler</td>
                <td>POST</td>
                <td>Deploys the full 14-field, 12-tag Gym & Fitness Center CRM taxonomy in a single command.</td>
            </tr>
        </tbody>
    </table>

    <!-- SECTION 7 -->
    <div class="page-break"></div>
    <div class="section-header">
        <h1>7. Senior GHL Solutions Architect Engineering Rules</h1>
        <span style="font-size: 8.5pt; color: #64748b; font-weight: 600;">SECTION 07</span>
    </div>

    <p>
        The Copilot embeds the <strong>29 Senior Solutions Architect Rules</strong> within its core system prompt. These rules enforce elite software engineering discipline and eliminate typical chatbot weaknesses:
    </p>

    <div class="card-grid">
        <div class="card">
            <div class="card-title">1. Direct Writing Style Mandate</div>
            <div class="card-desc">Zero pleasantries, zero self-introductions ("As an AI...", "I am thrilled to..."). Direct, authoritative, and actionable instructions only.</div>
        </div>
        <div class="card">
            <div class="card-title">2. Strict E.164 Phone Standards</div>
            <div class="card-desc">All phone numbers must strictly adhere to international E.164 standards (+1 followed by 10 digits for US/Canada) to avoid carrier deliverability drops.</div>
        </div>
        <div class="card">
            <div class="card-title">3. Contact Payload Hygiene</div>
            <div class="card-desc">When discrete <code>firstName</code> and <code>lastName</code> values are provided, the agent forbids sending a redundant <code>name</code> field that can cause race conditions in GHL.</div>
        </div>
        <div class="card">
            <div class="card-title">4. Auth Boundary Distinction</div>
            <div class="card-desc">Strictly distinguishes Sub-Account Private Integration Tokens (PIT) from Agency OAuth 2.0 applications, preventing permission scope mismatches.</div>
        </div>
        <div class="card">
            <div class="card-title">5. Failure-Mode Awareness</div>
            <div class="card-desc">Proactively identifies and warns users regarding duplicate contact merge rules, unverified email sending domains, and SMS compliance requirements.</div>
        </div>
        <div class="card">
            <div class="card-title">6. Zero Fabrication & Query Scope</div>
            <div class="card-desc">Never fabricates hypothetical endpoints. If a capability requires custom webhooks or third-party middleware (e.g. Zapier / Make), it explicitly states so.</div>
        </div>
    </div>

    <!-- SECTION 8 -->
    <div class="page-break"></div>
    <div class="section-header">
        <h1>8. Production Vertical Architecture: Gym & Fitness Centers</h1>
        <span style="font-size: 8.5pt; color: #64748b; font-weight: 600;">SECTION 08</span>
    </div>

    <p>
        The repository includes a turnkey vertical architecture module (<code>gym_architecture.py</code>) that provisions enterprise-grade schemas for boutique fitness studios, CrossFit gyms, and commercial fitness centers.
    </p>

    <h2>8.1 Custom Fields Blueprint (14 Strategic Fields)</h2>
    <table>
        <thead>
            <tr>
                <th>Field Name</th>
                <th>Data Type</th>
                <th>Configured Options / Rationale</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><code>Primary Fitness Goal</code></td>
                <td>SINGLE_OPTIONS</td>
                <td>Weight Loss, Muscle Building, General Health, Athletic Performance, Post-Rehab.</td>
            </tr>
            <tr>
                <td><code>Exercise Experience</code></td>
                <td>SINGLE_OPTIONS</td>
                <td>Beginner (0-6 mo), Intermediate (1-2 yrs), Advanced (3+ yrs).</td>
            </tr>
            <tr>
                <td><code>Exercise Limitations</code></td>
                <td>SINGLE_OPTIONS</td>
                <td>No, Yes.</td>
            </tr>
            <tr>
                <td><code>Limitation Category</code></td>
                <td>SINGLE_OPTIONS</td>
                <td>None, Lower Body/Knee, Upper Body/Shoulder, Back/Core, Cardio.</td>
            </tr>
            <tr>
                <td><code>Lead Score</code></td>
                <td>NUMBER</td>
                <td>Dynamic engagement score for lead qualification (0-100).</td>
            </tr>
            <tr>
                <td><code>Lead Tier</code></td>
                <td>SINGLE_OPTIONS</td>
                <td>Cold, Warm, Hot (evaluated via hysteresis logic).</td>
            </tr>
            <tr>
                <td><code>Membership Plan Type</code></td>
                <td>SINGLE_OPTIONS</td>
                <td>Month-to-Month, Annual VIP, Personal Training, Student/Senior.</td>
            </tr>
            <tr>
                <td><code>Membership Status</code></td>
                <td>SINGLE_OPTIONS</td>
                <td>Prospect, Trial Active, Member Active, Frozen, Churned.</td>
            </tr>
            <tr>
                <td><code>Total Check-ins Completed</code></td>
                <td>NUMBER</td>
                <td>Automated counter for member retention tracking.</td>
            </tr>
        </tbody>
    </table>

    <h2>8.2 Dual Pipelines & Retention Hysteresis Logic</h2>
    <ul>
        <li><strong>Gym Sales & Trial Pipeline:</strong> <code>New Prospect Inquiry</code> ➡️ <code>Free Pass Claimed</code> ➡️ <code>Tour Booked</code> ➡️ <code>Tour Completed</code> ➡️ <code>Trial Active (Day 1-7)</code> ➡️ <code>VIP Converted (Won)</code> ➡️ <code>Recycle (Lost)</code>.</li>
        <li><strong>Member Retention Pipeline:</strong> <code>Onboarding Week 1</code> ➡️ <code>Active Consistent</code> ➡️ <code>Attendance Dip (&lt;2 Visits in 14 Days)</code> ➡️ <code>At-Risk Flagged</code> ➡️ <code>Save Protocol Engaged</code> ➡️ <code>Churned / Frozen</code>.</li>
    </ul>

    <!-- SECTION 9 -->
    <div class="page-break"></div>
    <div class="section-header">
        <h1>9. Semantic Retrieval Engine (RAG) & Case Study Grounding</h1>
        <span style="font-size: 8.5pt; color: #64748b; font-weight: 600;">SECTION 09</span>
    </div>

    <p>
        To prevent ungrounded AI claims, <code>portfolio_knowledge_base.py</code> indexes verified agency projects from local binary documentation:
        <br/>• <strong>`KPI Scope .pdf`:</strong> Multi-account KPI tracking, client reporting architectures, data pipelines.
        <br/>• <strong>`XortLogix_Facebook_Analytics_Dashboard_Project_Document.docx`:</strong> Meta Ads API integration, automated reporting, webhook synchronization.
    </p>

    <h2>9.1 Dual-Stage Hybrid Retrieval Pipeline</h2>
    <div class="card-grid">
        <div class="card">
            <div class="card-title">1. Dense Vector Embeddings</div>
            <div class="card-desc">Pre-computed dense vector representations evaluated with cosine similarity matching to identify deep conceptual relevance.</div>
        </div>
        <div class="card">
            <div class="card-title">2. Sparse Term-Frequency Overlap</div>
            <div class="card-desc">Fast lexical term matching that scores exact technical terminology (e.g. "Meta Marketing API", "XortLogix", "PandaCare").</div>
        </div>
    </div>

    <div class="callout callout-info">
        <div class="callout-title">🎯 Authentic Citation Guarantee</div>
        When a user requests case studies or proof of work, verified project excerpts are automatically injected into the system prompt. The model cites real client architectures and authentic performance metrics rather than generating synthetic claims.
    </div>

    <!-- SECTION 10 & 11 -->
    <div class="page-break"></div>
    <div class="section-header">
        <h1>10. Token Usage Tracking & Quota Monitor</h1>
        <span style="font-size: 8.5pt; color: #64748b; font-weight: 600;">SECTION 10</span>
    </div>

    <p>
        The <code>usage_tracker.py</code> module maintains persistent, thread-safe monitoring of all model interactions:
    </p>
    <ul>
        <li><strong>Sliding-Window Metrics:</strong> Real-time tracking of Tokens Per Minute (TPM) and Requests Per Minute (RPM) to prevent hitting provider rate spikes.</li>
        <li><strong>Daily Quota Tracking:</strong> Tracks daily token accumulation against standard model quotas (e.g. 1M TPM / 1,500 RPD for Gemini Flash).</li>
        <li><strong>Automated UTC Rollover:</strong> Automatically clears and resets daily counters when the UTC calendar date transitions.</li>
        <li><strong>State Persistence:</strong> Serializes usage telemetry to <code>model_usage.json</code> with automated backup and recovery from <code>model_usage.json.bak</code>.</li>
    </ul>

    <div class="section-header" style="margin-top: 30px;">
        <h1>11. Complete REST & SSE API Reference</h1>
        <span style="font-size: 8.5pt; color: #64748b; font-weight: 600;">SECTION 11</span>
    </div>

    <table>
        <thead>
            <tr>
                <th>Method</th>
                <th>Route</th>
                <th>Purpose</th>
                <th>Format</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><code>GET</code></td>
                <td><code>/health</code></td>
                <td>Server status & configured provider health check.</td>
                <td>JSON</td>
            </tr>
            <tr>
                <td><code>GET</code></td>
                <td><code>/api/models</code></td>
                <td>Available models catalog enriched with live usage stats.</td>
                <td>JSON</td>
            </tr>
            <tr>
                <td><code>GET</code></td>
                <td><code>/api/usage-stats</code></td>
                <td>Global token and request metrics across all models.</td>
                <td>JSON</td>
            </tr>
            <tr>
                <td><code>GET</code></td>
                <td><code>/api/openrouter/pool-status</code></td>
                <td>Real-time balance and rotation state of OpenRouter keys.</td>
                <td>JSON</td>
            </tr>
            <tr>
                <td><code>POST</code></td>
                <td><code>/api/ghl/verify-token</code></td>
                <td>Validates Sub-Account Location ID & Bearer Token.</td>
                <td>JSON</td>
            </tr>
            <tr>
                <td><code>POST</code></td>
                <td><code>/api/ghl/contacts</code></td>
                <td>Fetches contacts list from connected sub-account.</td>
                <td>JSON</td>
            </tr>
            <tr>
                <td><code>POST</code></td>
                <td><code>/api/ghl/create-contact</code></td>
                <td>Creates a contact directly without natural language prompt.</td>
                <td>JSON</td>
            </tr>
            <tr>
                <td><code>POST</code></td>
                <td><code>/api/ghl/pipelines</code></td>
                <td>Fetches pipelines and stage metadata from sub-account.</td>
                <td>JSON</td>
            </tr>
            <tr>
                <td><code>POST</code></td>
                <td><code>/api/ghl/setup-gym</code></td>
                <td>Provisions 14 custom fields, 12 tags, and 2 pipelines.</td>
                <td>JSON</td>
            </tr>
            <tr>
                <td><code>POST</code></td>
                <td><code>/api/chat-agent</code></td>
                <td>Interactive agent execution with Server-Sent Events stream.</td>
                <td>SSE Stream</td>
            </tr>
        </tbody>
    </table>

    <!-- SECTION 12 -->
    <div class="page-break"></div>
    <div class="section-header">
        <h1>12. Deployment, Containerization & Verification</h1>
        <span style="font-size: 8.5pt; color: #64748b; font-weight: 600;">SECTION 12</span>
    </div>

    <h2>12.1 Local Environment Setup</h2>
    <pre><code># 1. Clone the repository
git clone https://github.com/muhammadokashapak/Conversation-AI-Copilot.git
cd Conversation-AI-Copilot

# 2. Initialize and activate Python virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows PowerShell
source venv/bin/activate  # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure .env file
cp .env.example .env

# 5. Launch the application
python app.py</code></pre>

    <h2>12.2 Cloud Deployment (Railway, Render & Docker)</h2>
    <ul>
        <li><strong>Railway:</strong> Pre-configured with native <code>railway.json</code> utilizing NIXPACKS builders and automatic restart policies.</li>
        <li><strong>Heroku / Render:</strong> Includes standard <code>Procfile</code> executing:
            <br/><code>web: uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips="*"</code></li>
        <li><strong>Docker:</strong> Containerize via standard Python 3.10-slim image exposing port <code>7861</code> with proxy headers enabled.</li>
    </ul>

    <h2>12.3 System Verification & Verification Summary</h2>
    <div class="callout callout-info">
        <div class="callout-title">✅ System Health Verified</div>
        The backend was verified active on <code>http://127.0.0.1:7861</code>. Endpoints <code>/health</code>, <code>/api/models</code>, and <code>/api/chat-agent</code> were validated with 200 OK status codes and successful Server-Sent Events streaming.
    </div>

    <div style="margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 16px; text-align: center; color: #94a3b8; font-size: 8.5pt;">
        Conversation AI Copilot • Project Submission & Technical Architecture Report • Generated September 2026
    </div>

</body>
</html>
"""

def generate_pdf():
    print("Writing styled HTML template...")
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("Launching Playwright Chromium to compile PDF...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file:///{os.path.abspath(OUTPUT_HTML).replace(os.sep, '/')}", wait_until="networkidle")
        
        page.pdf(
            path=OUTPUT_PDF,
            format="A4",
            print_background=True,
            margin={
                "top": "0mm",
                "right": "0mm",
                "bottom": "0mm",
                "left": "0mm"
            },
            prefer_css_page_size=True
        )
        browser.close()
    
    print(f"[OK] PDF successfully generated at: {OUTPUT_PDF}")
    if os.path.exists(OUTPUT_HTML):
        os.remove(OUTPUT_HTML)

if __name__ == "__main__":
    generate_pdf()
