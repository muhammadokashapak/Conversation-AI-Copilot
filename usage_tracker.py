import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

USAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_usage.json")

# Verified Real Limits (Free / Standard Tier Specs)
MODEL_SPECS: Dict[str, Dict[str, Any]] = {
    # Google Gemini Models
    "gemini-3.6-flash": {
        "tpm_limit": 1000000,
        "rpm_limit": 15,
        "rpd_limit": 1500,
        "badge_capacity": "1M TPM • 15 RPM"
    },
    "gemini-3.7-flash": {
        "tpm_limit": 1000000,
        "rpm_limit": 15,
        "rpd_limit": 1000,
        "badge_capacity": "1M TPM • 15 RPM"
    },
    "gemini-3.5-flash": {
        "tpm_limit": 1000000,
        "rpm_limit": 15,
        "rpd_limit": 1500,
        "badge_capacity": "1M TPM • 15 RPM"
    },
    "gemini-flash-latest": {
        "tpm_limit": 1000000,
        "rpm_limit": 15,
        "rpd_limit": 1500,
        "badge_capacity": "1M TPM • 15 RPM"
    },

    # Groq Cloud Ultra-Fast Models
    "groq/compound-mini": {
        "tpm_limit": 70000,
        "rpm_limit": 30,
        "rpd_limit": 14400,
        "badge_capacity": "70k TPM • 30 RPM"
    },
    "groq/compound": {
        "tpm_limit": 70000,
        "rpm_limit": 30,
        "rpd_limit": 14400,
        "badge_capacity": "70k TPM • 30 RPM"
    },
    "qwen/qwen3.8-27b": {
        "tpm_limit": 8000,
        "rpm_limit": 30,
        "rpd_limit": 14400,
        "badge_capacity": "8k TPM • 30 RPM"
    },
    "qwen/qwen3.6-27b": {
        "tpm_limit": 8000,
        "rpm_limit": 30,
        "rpd_limit": 14400,
        "badge_capacity": "8k TPM • 30 RPM"
    },
    "openai/gpt-oss-120b": {
        "tpm_limit": 8000,
        "rpm_limit": 30,
        "rpd_limit": 14400,
        "badge_capacity": "8k TPM • 30 RPM"
    },
    "openai/gpt-oss-20b": {
        "tpm_limit": 8000,
        "rpm_limit": 30,
        "rpd_limit": 14400,
        "badge_capacity": "8k TPM • 30 RPM"
    },
    "allam-2-7b": {
        "tpm_limit": 8000,
        "rpm_limit": 30,
        "rpd_limit": 14400,
        "badge_capacity": "8k TPM • 30 RPM"
    },

    # RapidAPI Free ChatGPT Gateway
    "rapidapi-chatgpt": {
        "tpm_limit": 10000,
        "rpm_limit": 10,
        "rpd_limit": 100,
        "badge_capacity": "10k TPM • 10 RPM"
    }
}


class ModelUsageTracker:
    def __init__(self):
        self.usage_file = USAGE_FILE
        self.sliding_window: Dict[str, List[Dict[str, Any]]] = {}  # {model_id: [{"ts": time, "tokens": int}]}
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

    def record_usage(self, model_id: str, prompt_tokens: int = 0, completion_tokens: int = 0):
        """
        Records tokens from a request into both daily persistent stats and the 60-second real-time TPM sliding window.
        """
        now = time.time()
        total_tokens = max(10, prompt_tokens + completion_tokens)
        current_day = self._get_current_day()

        # Update in-memory sliding window
        if model_id not in self.sliding_window:
            self.sliding_window[model_id] = []
        
        self.sliding_window[model_id].append({
            "ts": now,
            "tokens": total_tokens
        })
        # Clean events older than 120 seconds
        self.sliding_window[model_id] = [
            ev for ev in self.sliding_window[model_id] if now - ev["ts"] <= 120
        ]

        # Update persistent daily metrics
        if self.data.get("current_day") != current_day:
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
        m_stat["total_tokens"] += total_tokens
        m_stat["daily_tokens"] += total_tokens
        m_stat["last_used"] = datetime.now(timezone.utc).isoformat()

        self._save()

    def get_model_stats(self, model_id: str) -> Dict[str, Any]:
        """
        Returns live real-time TPM, RPM, and Daily usage percentages for the requested model.
        """
        now = time.time()
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

        spec = MODEL_SPECS.get(model_id, {
            "tpm_limit": 70000,
            "rpm_limit": 30,
            "rpd_limit": 1000,
            "badge_capacity": "Standard"
        })

        # Calculate current minute TPM (tokens in last 60 seconds)
        events = self.sliding_window.get(model_id, [])
        recent_events = [ev for ev in events if now - ev["ts"] <= 60]
        current_minute_tokens = sum(ev["tokens"] for ev in recent_events)
        current_minute_requests = len(recent_events)

        tpm_limit = spec["tpm_limit"]
        rpm_limit = spec["rpm_limit"]
        rpd_limit = spec["rpd_limit"]

        # Live Real-Time TPM percentage
        tpm_usage_pct = min(100.0, round((current_minute_tokens / tpm_limit) * 100, 1))
        
        # Daily request percentage
        daily_req = model_stat.get("daily_requests", 0)
        daily_usage_pct = min(100.0, round((daily_req / rpd_limit) * 100, 1))

        # The active operational usage percentage is primarily driven by current minute TPM load, with daily quota fallback
        effective_usage_pct = max(tpm_usage_pct, daily_usage_pct)
        remaining_pct = max(0.0, round(100.0 - effective_usage_pct, 1))

        # Status text and health color
        if tpm_usage_pct >= 85:
            status = f"⚠️ TPM Near Capacity ({current_minute_tokens:,} / {tpm_limit:,})"
            health_color = "#ef4444"
        elif tpm_usage_pct > 0:
            status = f"Active ({current_minute_tokens:,} TPM used • cools in 60s)"
            health_color = "#f59e0b"
        elif daily_usage_pct >= 90:
            status = "Daily Request Cap Approaching"
            health_color = "#ef4444"
        else:
            status = f"100% Ready ({spec['badge_capacity']})"
            health_color = "#10b981"

        return {
            "model_id": model_id,
            "current_minute_tokens": current_minute_tokens,
            "tpm_limit": tpm_limit,
            "tpm_usage_pct": tpm_usage_pct,
            "current_minute_requests": current_minute_requests,
            "rpm_limit": rpm_limit,
            "daily_requests": daily_req,
            "daily_limit": rpd_limit,
            "daily_tokens": model_stat.get("daily_tokens", 0),
            "total_requests": model_stat.get("total_requests", 0),
            "total_tokens": model_stat.get("total_tokens", 0),
            "usage_percentage": effective_usage_pct,
            "remaining_percentage": remaining_pct,
            "status": status,
            "health_color": health_color,
            "badge_capacity": spec["badge_capacity"],
            "last_used": model_stat.get("last_used")
        }


# Global singleton instance
usage_tracker = ModelUsageTracker()
