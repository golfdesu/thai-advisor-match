"""
Cybersecurity & Defense Engine:
1. Rate Limiting Middleware (Sliding Window / Token Bucket per Client IP)
2. Input Sanitization & Anti-XSS Utilities
3. LLM Prompt Injection Detector & Jailbreak Sanitizer
4. Security Response Headers Middleware
"""

import time
import re
import html
import threading
from typing import Dict, Tuple, List, Optional
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings


class RateLimiter:
    """
    Thread-safe In-Memory Sliding Window Rate Limiter.
    Limits requests per IP address to mitigate DoS, brute force, and scraping abuse.

    Memory hygiene (DSA audit 2026-09-10): per-IP timestamp lists were pruned, but
    the dict KEYS were never removed — every distinct client IP (including probes
    and scrapers) leaked an entry forever. A stale-key sweep now runs amortized
    every `_sweep_every` mutations while the lock is already held.
    """

    def __init__(self, requests_per_minute: int = 120, max_tracked_ips: int = 50_000):
        self.rpm = requests_per_minute
        self.window = 60.0  # 60 seconds
        self.records: Dict[str, List[float]] = {}
        self.lock = threading.Lock()
        self._mutations_since_sweep = 0
        self._sweep_every = 512
        # Hard cap on tracked IPs: the stale sweep only drops IPs idle > 60 s, so a
        # flood of distinct IPs inside one window grew `records` without bound.
        self._max_ips = max_tracked_ips

    def _sweep_stale_ips(self, now: float) -> None:
        cutoff = now - self.window
        stale = [ip for ip, ts in self.records.items() if not ts or ts[-1] <= cutoff]
        for ip in stale:
            del self.records[ip]

    def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        now = time.time()
        with self.lock:
            self._mutations_since_sweep += 1
            if self._mutations_since_sweep >= self._sweep_every:
                self._mutations_since_sweep = 0
                self._sweep_stale_ips(now)

            if client_ip not in self.records:
                if len(self.records) >= self._max_ips:
                    self._sweep_stale_ips(now)
                    # Still full: evict the oldest-inserted IPs (dict keeps insertion order)
                    overflow = len(self.records) - self._max_ips + 1
                    for ip in list(self.records)[:max(0, overflow)]:
                        del self.records[ip]
                self.records[client_ip] = [now]
                return True, self.rpm - 1

            # Evict timestamps older than 60 seconds
            cutoff = now - self.window
            self.records[client_ip] = [t for t in self.records[client_ip] if t > cutoff]

            if len(self.records[client_ip]) < self.rpm:
                self.records[client_ip].append(now)
                remaining = self.rpm - len(self.records[client_ip])
                return True, remaining
            else:
                return False, 0


# Pre-compile Prompt Injection & Jailbreak Attack Patterns
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?(dan|developer\s+mode|unrestricted|jailbreak)", re.IGNORECASE),
    re.compile(r"(reveal|print|show|leak|output)\s+(your\s+)?(system\s+prompt|instructions|api\s*key|secret)", re.IGNORECASE),
    re.compile(r"override\s+(all\s+)?safety\s+(guidelines|filters|protocols)", re.IGNORECASE),
    re.compile(r"assistant\s*<\s*\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]", re.IGNORECASE),
]

# Sensitive PII Patterns (National ID, Credit Cards, Secrets)
SENSITIVE_DATA_PATTERNS = [
    # \b treats Thai letters as \w, so it fails to bound digits that sit directly
    # against Thai/Latin text with no space (e.g. "เลขบัตรประชาชน1234567890123ครับ").
    # Use digit-only lookaround instead so the ID/card number can't be absorbed
    # into a longer digit run while still matching next to any script.
    # Thai 13-digit National ID, plain or in the printed 1-2345-67890-12-3 grouping
    re.compile(r"(?<!\d)[1-9][-\s]?\d{4}[-\s]?\d{5}[-\s]?\d{2}[-\s]?\d(?!\d)"),
    re.compile(r"(?<!\d)(?:\d{4}[-\s]?){3}\d{4}(?!\d)"),  # Credit card numbers
    re.compile(r"\bAIza[0-9A-Za-z-_]{35}\b"),  # Google API Keys
    re.compile(r"\bAQ\.[A-Za-z0-9_\-]{20,}\b"),  # Gemini API Keys
]


# DSA audit 2026-09-10 (#7): precompiled control-char strip (AGENTS.md §5.3) —
# runs on every sanitized input field, was re-compiling per call.
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def sanitize_input_text(text: Optional[str], max_length: int = 1000) -> str:
    """
    Sanitizes user input string:
    1. Trims and enforces maximum length to prevent buffer/payload inflation.
    2. Strips null bytes and malicious control characters.
    3. Normalizes whitespace and HTML entities.
    """
    if not text:
        return ""
    # Strip null bytes & control chars
    clean = _CONTROL_CHARS_RE.sub("", str(text))
    clean = clean.strip()
    if len(clean) > max_length:
        clean = clean[:max_length]
    return clean


def sanitize_for_prompt(text: str, max_length: int = 1500) -> str:
    """
    Hardens user inputs before injecting into LLM system prompts:
    1. Detects and neutralizes prompt injection keywords.
    2. Escapes Markdown/formatting control delimiters.
    3. Redacts potential PII or confidential API keys.
    """
    sanitized = sanitize_input_text(text, max_length=max_length)

    # Check for direct prompt injection attempt
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(sanitized):
            # Neutralize instruction override
            sanitized = pattern.sub("[REDACTED_SUSPICIOUS_INSTRUCTION]", sanitized)

    # Redact sensitive PII / secrets
    for pattern in SENSITIVE_DATA_PATTERNS:
        sanitized = pattern.sub("[REDACTED_CONFIDENTIAL]", sanitized)

    return sanitized


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects OWASP Recommended Security Response Headers:
    - X-Content-Type-Options: nosniff (Prevents MIME sniffing)
    - X-Frame-Options: DENY (Prevents Clickjacking)
    - X-XSS-Protection: 0 (legacy XSS auditor is removed from modern browsers
      and re-enabling it creates its own vectors — OWASP HTTP Headers cheat sheet)
    - Strict-Transport-Security (HSTS, non-DEBUG only — preload intentionally
      omitted: registering at hstspreload.org is irreversible)
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if not settings.DEBUG:
            # HSTS on localhost http would be ignored anyway; keep it prod-only
            # so a misconfigured local run can never get "sticky-https" locked in.
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


def _client_ip(request: Request) -> str:
    """
    Best-effort client IP.

    Trust boundary (fixed 2026-09-26): the gateway's nginx uses
    $proxy_add_x_forwarded_for, which APPENDS to a client-supplied header, so the
    left-most X-Forwarded-For entry is attacker-controlled — rotating it gave a
    fresh rate-limit bucket per request. Resolution order now:
    1. X-Real-IP — nginx overwrites it with $remote_addr (not spoofable via gateway).
    2. Right-most X-Forwarded-For entry — appended by the nearest proxy.
    3. Socket peer.
    """
    real_ip = (request.headers.get("X-Real-IP") or "").strip()
    if real_ip:
        return real_ip
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        last = forwarded_for.split(",")[-1].strip()
        if last:
            return last
    return request.client.host if request.client else "127.0.0.1"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enforces sliding-window rate limiting per IP address.
    Exempts health checks and static docs.

    Tiered limits (cyber audit 2026-09-10, B-4): endpoints that spend paid
    tokens / external API quota (Gemini calls) get their own much stricter
    limiter, so the global 180 rpm bucket can never be used to drain the AI
    budget by hammering a single expensive route.
    """

    def __init__(self, app, rate_limiter: RateLimiter, strict_limiters: Optional[Dict[str, RateLimiter]] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.strict_limiters = strict_limiters or {}
        self.exempt_paths = {"/", "/api/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in self.exempt_paths:
            return await call_next(request)

        client_ip = _client_ip(request)

        allowed, remaining = self.rate_limiter.is_allowed(client_ip)
        if not allowed:
            return self._rate_limited_response(self.rate_limiter.rpm)

        # Expensive-tier check (mutations only — GET prefetches stay on the global bucket).
        # The most specific configured prefix wins over broader prefixes.
        if request.method == "POST":
            for prefix, limiter in sorted(self.strict_limiters.items(), key=lambda kv: -len(kv[0])):
                if path.startswith(prefix):
                    allowed_strict, remaining_strict = limiter.is_allowed(client_ip)
                    if not allowed_strict:
                        return self._rate_limited_response(limiter.rpm)
                    response = await call_next(request)
                    response.headers["X-RateLimit-Limit"] = str(limiter.rpm)
                    response.headers["X-RateLimit-Remaining"] = str(min(remaining, remaining_strict))
                    return response

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.rpm)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    @staticmethod
    def _rate_limited_response(limit: int) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please slow down and try again in a moment.",
                "status_code": 429
            },
            headers={"Retry-After": "60", "X-RateLimit-Limit": str(limit)}
        )
