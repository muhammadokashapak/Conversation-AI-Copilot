import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any

USAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_usage.json")

# Default daily limits for models to compute realistic percentage usage
DEFAULT_DAILY_LIMITS = {
    # Gemini Tier
    "gemini-3.6-flash": 1500,
    "gemini-3.7-flash": 1000,
    "gemini-3.5-flash": 1500,
    "gemini-2.5-flash": 1500,
    "gemini-2.5-pro": 500,
    
    # Groq LPU Tier
    "qwen/qwen3.8-27b": 1000,
    "qwen/qwen3.6-27b": 1000,
    "openai/gpt-oss-20b": 1000,
    "allam-2-7b": 1000,

    # OpenRouter Free Tier
    "inclusionai/ling-3.0-flash-fin:free": 100,
    "dots-studio/dots-3-note-preview:free": 100,
    "liquid/lfm-2.5-2.6b:free": 100,
    "google/gemma-4-26b-a4b-it:free": 100,

    # OpenRouter xAI & Flagship (credits/requests tracking)
    "x-ai/grok-4.6": 200,
    "x-ai/grok-4.5": 200,
    "x-ai/grok-4.3": 250,
    "deepseek/deepseek-v4-flash": 300,
    "deepseek/deepseek-v4-pro": 200,
    "deepseek/deepseek-v3.2": 250,
    "anthropic/claude-3.5-sonnet": 100,
    "openai/gpt-4o": 150,
    "openai/gpt-4o-mini": 500,
    "meta-llama/llama-3.3-70b-instruct": 200
}


class ModelUsageTracker:
    def __init__(self):
        self.usage_file = USAGE_FILE
        self.data = self._load()

    def _get_current_day(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"current_day": self._get_current_day(), "models": {}}

    def _save(self):
        try:
            with open(self.usage_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    def record_usage(self, model_id: str, tokens_est: int = 150):
        current_day = self._get_current_day()
        if self.data.get("current_day") != current_day:
            # Reset daily counters on a new day
            self.data["current_day"] = current_day
            for m in self.data.get("models", {}).values():
                m["daily_requests"] = 0
                m["daily_tokens"] = 0

        if "models" not in self.data:
            self.data["models"] = {}

        if model_id not in self.data["models"]:
            self.data["models"][model_id] = {
                "total_requests": 0,
                "daily_requests": 0,
                "total_tokens": 0,
                "daily_tokens": 0,
                "last_used": ""
            }

        m_stat = self.data["models"][model_id]
        m_stat["total_requests"] += 1
        m_stat["daily_requests"] += 1
        m_stat["total_tokens"] += tokens_est
        m_stat["daily_tokens"] += tokens_est
        m_stat["last_used"] = datetime.now(timezone.utc).isoformat()

        self._save()

    def get_model_stats(self, model_id: str) -> Dict[str, Any]:
        current_day = self._get_current_day()
        if self.data.get("current_day") != current_day:
            self.data["current_day"] = current_day
            for m in self.data.get("models", {}).values():
                m["daily_requests"] = 0
                m["daily_tokens"] = 0

        model_stat = self.data.get("models", {}).get(model_id, {
            "total_requests": 0,
            "daily_requests": 0,
            "total_tokens": 0,
            "daily_tokens": 0,
            "last_used": None
        })

        daily_req = model_stat.get("daily_requests", 0)
        daily_limit = DEFAULT_DAILY_LIMITS.get(model_id, 200)

        usage_pct = min(100.0, round((daily_req / daily_limit) * 100, 1))
        remaining_pct = max(0.0, round(100.0 - usage_pct, 1))

        if usage_pct < 60:
            status = "Healthy / High Quota"
            health_color = "#10b981"
        elif usage_pct < 85:
            status = "Moderate Usage"
            health_color = "#f59e0b"
        else:
            status = "High Usage"
            health_color = "#ef4444"

        return {
            "daily_requests": daily_req,
            "daily_limit": daily_limit,
            "daily_tokens": model_stat.get("daily_tokens", 0),
            "total_requests": model_stat.get("total_requests", 0),
            "total_tokens": model_stat.get("total_tokens", 0),
            "usage_percentage": usage_pct,
            "remaining_percentage": remaining_pct,
            "status": status,
            "health_color": health_color,
            "last_used": model_stat.get("last_used")
        }


# Global singleton instance
usage_tracker = ModelUsageTracker()
