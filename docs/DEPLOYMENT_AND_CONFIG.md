# 🚀 Deployment & Configuration Guide
## Conversation AI Copilot for GoHighLevel (GHL)

This document provides complete instructions for configuring, deploying, and maintaining the **Conversation AI Copilot** across local, containerized, and cloud hosting environments.

---

## 1. Environment Variables Configuration (`.env`)

Create a `.env` file in the project root directory (or configure these variables in your cloud provider's dashboard):

```bash
cp .env.example .env
```

### Full Configuration Reference:

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | Recommended | — | Single Google Gemini API key from Google AI Studio. |
| `GEMINI_API_KEYS` | Optional | — | Comma-separated list of Gemini API keys for auto-rotation and failover. |
| `GROQ_API_KEY` | Recommended | — | Groq Cloud API key for ultra-fast LPU inference (`gsk_...`). |
| `OPENROUTER_API_KEY` | Optional | — | OpenRouter API key for xAI Grok, DeepSeek, Claude, and free models. |
| `OPENROUTER_API_KEYS`| Optional | — | Comma-separated list of OpenRouter keys for automated balance polling. |
| `RAPIDAPI_KEY` | Optional | — | RapidAPI key for fallback conversational endpoints. |
| `RAPIDAPI_HOST` | Optional | `free-chatgpt-api.p.rapidapi.com` | RapidAPI host endpoint. |
| `PORT` | Optional | `7861` | Port on which the FastAPI application binds. |
| `HOST` | Optional | `0.0.0.0` | Host IP binding address (`0.0.0.0` for containers, `127.0.0.1` for local). |

---

## 2. Local Development Setup

### 2.1 Requirements:
- Python 3.10 or higher
- Git
- Active internet connection for API endpoints

### 2.2 Setup Instructions:

```bash
# 1. Clone repository
git clone https://github.com/muhammadokashapak/Conversation-AI-Copilot.git
cd Conversation-AI-Copilot

# 2. Create Python virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\activate
# On macOS / Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Launch the application
python app.py
```

Open your browser to:
👉 **`http://127.0.0.1:7861`**

---

## 3. Production Deployment Options

### 3.1 Deploying on Railway

The repository includes a native `railway.json` pre-configured for NIXPACKS:

1. Push your repository to GitHub.
2. Log into [Railway.app](https://railway.app).
3. Click **New Project** ➡️ **Deploy from GitHub Repo**.
4. Select `Conversation-AI-Copilot`.
5. Under **Variables**, add your `GEMINI_API_KEY`, `GROQ_API_KEY`, etc.
6. Railway automatically executes the start command defined in `railway.json`:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'
   ```
7. Generate a public domain under service **Settings** ➡️ **Networking**.

---

### 3.2 Deploying on Heroku / Render

The project includes a standard `Procfile`:
```text
web: uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips="*"
```

- **Render**: Create a **New Web Service**, connect repo, set runtime to **Python 3**, build command `pip install -r requirements.txt`, start command `uvicorn app:app --host 0.0.0.0 --port $PORT`. Add environment variables in the dashboard.
- **Heroku**: Create an app, add the `heroku/python` buildpack, and push to `heroku master`.

---

### 3.3 Deploying with Docker

You can containerize the application using this standard `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 7861

# Run server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7861", "--proxy-headers"]
```

#### Build and Run Container:
```bash
# Build Docker image
docker build -t conversation-ai-copilot .

# Run container with environment file
docker run -d -p 7861:7861 --env-file .env --name ghl-copilot conversation-ai-copilot
```

---

### 3.4 Production Reverse Proxy (Nginx + SSL)

When hosting on a Linux VPS (e.g., Ubuntu 22.04 LTS), use Nginx as a reverse proxy with Let's Encrypt SSL:

```nginx
server {
    server_name copilot.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:7861;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Critical for Server-Sent Events (SSE) Streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

> [!IMPORTANT]
> For Server-Sent Events (`/api/chat-agent`) to stream tokens in real-time through Nginx, `proxy_buffering off;` and `proxy_read_timeout 86400s;` are **mandatory**. Without disabling buffering, tokens will buffer until completion rather than streaming interactively.

---

## 4. Monitoring & Troubleshooting

### 4.1 Port Already in Use (`[Errno 10048]`)
If port `7861` is already in use by a previous instance:

- **Windows (PowerShell)**:
  ```powershell
  # Find PID
  Get-NetTCPConnection -LocalPort 7861 | Select-Object OwningProcess
  # Kill process
  Stop-Process -Id <PID> -Force
  ```
- **Linux / macOS**:
  ```bash
  lsof -ti :7861 | xargs kill -9
  ```

### 4.2 Rate Limiting (`HTTP 429`) & Key Failover
If you encounter `429 Too Many Requests` on Google Gemini or Groq:
1. Configure `GEMINI_API_KEYS` with multiple comma-separated keys in your `.env`.
2. The built-in `GeminiKeyPool` automatically quarantines the rate-limited key for 65 seconds and shifts to the next healthy key in the pool.
3. Switch models in the UI dropdown to **Groq Compound Mini** or **Groq Qwen 3.8 27B** for instantaneous LPU inference without quota blocks.
