"""
Key Pool Manager for OpenRouter and AI Providers.
Provides intelligent key polling, credit tracking, automatic shifting on quota depletion (402/429),
and seamless failover across multiple API keys.
"""

import os
import time
import json
import logging
import threading
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger("key_pool_manager")
logger.setLevel(logging.INFO)


class OpenRouterKeyPool:
    """
    Manages a pool of OpenRouter API keys with auto-polling, credit monitoring,
    and automatic shifting to healthy keys when credits are low or exhausted.
    """
    def __init__(self, keys: Optional[List[str]] = None):
        self._lock = threading.Lock()
        self.keys_state: List[Dict[str, Any]] = []
        self._current_index = 0
        
        raw_keys = keys or []
        # Also parse from environment if not explicitly passed
        if not raw_keys:
            env_pool = os.getenv("OPENROUTER_API_KEYS", "").strip()
            single_key = os.getenv("OPENROUTER_API_KEY", "").strip()
            if env_pool:
                raw_keys.extend([k.strip() for k in env_pool.split(",") if k.strip()])
            elif single_key:
                raw_keys.append(single_key)
        
        self.set_keys(raw_keys)

    def set_keys(self, raw_keys: List[str]):
        """Initializes or updates the pool with a list of API keys."""
        with self._lock:
            seen = set()
            clean_keys = []
            for k in raw_keys:
                k_clean = k.strip()
                if k_clean and k_clean not in seen and k_clean.startswith("sk-or-v1-"):
                    seen.add(k_clean)
                    clean_keys.append(k_clean)

            self.keys_state = []
            for k in clean_keys:
                self.keys_state.append({
                    "key": k,
                    "masked": f"{k[:16]}...{k[-4:]}",
                    "is_active": True,
                    "is_depleted": False,
                    "total_credits": 0.0,
                    "total_usage": 0.0,
                    "remaining_credits": 0.0,
                    "last_status_code": 200,
                    "last_error": "",
                    "last_checked": 0,
                    "success_count": 0,
                    "failure_count": 0
                })
            
            self._current_index = 0
            logger.info(f"OpenRouterKeyPool initialized with {len(self.keys_state)} keys.")

    def get_active_key(self) -> Optional[str]:
        """Returns the currently active, healthy API key from the pool."""
        with self._lock:
            if not self.keys_state:
                return None
            
            # Find the first available healthy key starting from current index
            n = len(self.keys_state)
            for i in range(n):
                idx = (self._current_index + i) % n
                entry = self.keys_state[idx]
                if entry["is_active"] and not entry["is_depleted"]:
                    self._current_index = idx
                    return entry["key"]
            
            # If all are marked depleted, reset and try the least failed key
            logger.warning("All OpenRouter keys in pool were marked depleted. Resetting pool for fresh retry...")
            for entry in self.keys_state:
                entry["is_depleted"] = False
            
            self._current_index = 0
            return self.keys_state[0]["key"]

    def mark_key_depleted(self, key: str, status_code: int = 402, error_msg: str = ""):
        """
        Marks a specific key as depleted or rate-limited, and shifts the active
        key pointer to the next available healthy key.
        """
        with self._lock:
            for entry in self.keys_state:
                if entry["key"] == key:
                    entry["is_depleted"] = True
                    entry["last_status_code"] = status_code
                    entry["last_error"] = error_msg
                    entry["failure_count"] += 1
                    logger.warning(
                        f"OpenRouter Key {entry['masked']} marked DEPLETED (Status {status_code}: {error_msg}). "
                        f"Shifting to next available key in pool."
                    )
            
            # Advance to next available healthy key
            n = len(self.keys_state)
            for i in range(1, n + 1):
                idx = (self._current_index + i) % n
                if not self.keys_state[idx]["is_depleted"]:
                    self._current_index = idx
                    logger.info(f"OpenRouterKeyPool shifted to key: {self.keys_state[idx]['masked']}")
                    return

    def record_success(self, key: str):
        """Records a successful API call for the given key."""
        with self._lock:
            for entry in self.keys_state:
                if entry["key"] == key:
                    entry["success_count"] += 1
                    entry["is_depleted"] = False
                    entry["last_error"] = ""
                    entry["last_status_code"] = 200

    def poll_key_credits(self, key_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Polls OpenRouter /api/v1/credits to fetch live balance."""
        key = key_entry["key"]
        headers = {"Authorization": f"Bearer {key}"}
        try:
            resp = requests.get("https://openrouter.ai/api/v1/credits", headers=headers, timeout=6)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                total_credits = float(data.get("total_credits", 0.0) or 0.0)
                total_usage = float(data.get("total_usage", 0.0) or 0.0)
                remaining = max(0.0, total_credits - total_usage) if total_credits > 0 else 0.0
                
                key_entry["total_credits"] = total_credits
                key_entry["total_usage"] = total_usage
                key_entry["remaining_credits"] = remaining
                key_entry["last_checked"] = time.time()
                key_entry["last_status_code"] = 200
                
                # If credits exhausted, mark accordingly
                if total_credits > 0 and remaining <= 0.001:
                    key_entry["is_depleted"] = True
                else:
                    key_entry["is_depleted"] = False
                
                return {"success": True, "remaining": remaining, "usage": total_usage}
            elif resp.status_code in [401, 402, 429]:
                key_entry["is_depleted"] = True
                key_entry["last_status_code"] = resp.status_code
                key_entry["last_error"] = f"HTTP {resp.status_code}"
                return {"success": False, "status_code": resp.status_code}
        except Exception as e:
            logger.debug(f"Polling error for key {key_entry['masked']}: {e}")
        return {"success": False}

    def poll_all_keys(self):
        """Polls and updates status for all keys in the pool."""
        with self._lock:
            entries = list(self.keys_state)
        for entry in entries:
            self.poll_key_credits(entry)

    def get_pool_status(self) -> List[Dict[str, Any]]:
        """Returns public status summary of all keys in the pool."""
        with self._lock:
            summary = []
            for idx, entry in enumerate(self.keys_state):
                summary.append({
                    "index": idx,
                    "masked_key": entry["masked"],
                    "is_current": (idx == self._current_index),
                    "is_active": entry["is_active"],
                    "is_depleted": entry["is_depleted"],
                    "total_usage": round(entry["total_usage"], 4),
                    "total_credits": round(entry["total_credits"], 4),
                    "remaining_credits": round(entry["remaining_credits"], 4),
                    "last_status_code": entry["last_status_code"],
                    "success_count": entry["success_count"],
                    "failure_count": entry["failure_count"]
                })
            return summary


def _init_default_pool() -> OpenRouterKeyPool:
    env_keys_str = os.getenv("OPENROUTER_API_KEYS", "")
    keys_list = [k.strip() for k in env_keys_str.split(",") if k.strip()]
    if not keys_list:
        single_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if single_key:
            keys_list = [single_key]
    return OpenRouterKeyPool(keys_list)


# Global singleton instance loaded dynamically from environment
openrouter_key_pool = _init_default_pool()

