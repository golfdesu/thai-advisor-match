# -*- coding: utf-8 -*-
"""
Fetch OpenAlex metrics and handle polite rate-limits without crashing when API keys expire.
Falls back seamlessly to polite unauthenticated tier (mailto header).
"""

import os
import re
import time
import json
import itertools
import threading
import urllib.request
import urllib.parse
import ssl
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend/.env is reliably loaded regardless of execution working directory
_backend_env = Path(__file__).resolve().parent.parent / ".env"
if _backend_env.exists():
    load_dotenv(dotenv_path=_backend_env)
else:
    load_dotenv()

# Keep certificate and hostname verification enabled for all OpenAlex requests.
SSL_CTX = ssl.create_default_context()

# API Key Pool with Automatic Round-Robin & Auto-Failover.
# Without configured keys, fetch_with_retry uses the polite unauthenticated tier.
raw_keys_env = os.getenv("OPENALEX_API_KEYS") or os.getenv("OPENALEX_API_KEY", "")
API_KEYS_POOL = [k.strip() for k in raw_keys_env.split(",") if k.strip()]
if not API_KEYS_POOL:
    print(
        "⚠️ OPENALEX_API_KEYS / OPENALEX_API_KEY not set; "
        "using the polite unauthenticated tier.",
        flush=True,
    )

EXHAUSTED_KEYS = set()
KEY_LOCK = threading.Lock()
_key_cycle = itertools.cycle(API_KEYS_POOL)

def get_next_api_key() -> str | None:
    """Thread-safe round-robin selection. If all keys exhausted, returns None to use polite tier."""
    with KEY_LOCK:
        active_keys = [k for k in API_KEYS_POOL if k not in EXHAUSTED_KEYS]
        if not active_keys:
            return None
        for _ in range(len(API_KEYS_POOL)):
            candidate = next(_key_cycle)
            if candidate not in EXHAUSTED_KEYS:
                return candidate
        return active_keys[0]

def mark_key_exhausted(api_key: str):
    """Mark an API key as exhausted so traffic instantly redirects to healthy keys or polite pool"""
    with KEY_LOCK:
        if api_key and api_key not in EXHAUSTED_KEYS:
            EXHAUSTED_KEYS.add(api_key)
            remaining = len(API_KEYS_POOL) - len(EXHAUSTED_KEYS)
            # ascii-safe: Windows consoles (cp1252/cp874) crash on emoji
            print(f"\n[!] Key ...{api_key[-6:]} reached daily quota! "
                  f"Active keys remaining: {remaining} (Falling back to polite pool)",
                  flush=True)


def all_keys_exhausted() -> bool:
    """Return True if all configured API keys have hit their daily quota."""
    with KEY_LOCK:
        return len(API_KEYS_POOL) > 0 and len(EXHAUSTED_KEYS) >= len(API_KEYS_POOL)

OPENALEX_HEADERS = {
    "User-Agent": "ThaiEduCenterAcademicMatcher/2.0 (mailto:golf_chayanon@hotmail.com)"
}

def append_api_key(url: str, api_key: str | None) -> str:
    """Safely append selected OpenAlex API key to request URL if present"""
    if not api_key:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}api_key={api_key}"

def fetch_with_retry(url: str, max_retries: int = 3) -> dict:
    """Fetch URL with key failover, polite fallback, and backoff"""
    for attempt in range(max_retries):
        current_key = get_next_api_key()
        authed_url = append_api_key(url, current_key)
        try:
            req = urllib.request.Request(authed_url, headers=OPENALEX_HEADERS)
            with urllib.request.urlopen(req, timeout=6, context=SSL_CTX) as res:
                return json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                if current_key:
                    mark_key_exhausted(current_key)
                    continue
                time.sleep(1.0 * (attempt + 1))
            elif e.code >= 500:
                time.sleep(1.0)
            else:
                return {}
        except Exception:
            time.sleep(0.5)
    return {}
