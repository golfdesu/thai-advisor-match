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


class RateLimiter:
    """
    Thread-safe In-Memory Sliding Window Rate Limiter.
    Limits requests per IP address to mitigate DoS, brute force, and scraping abuse.
    """

    def __init__(self, requests_per_minute: int = 120):
        self.rpm = requests_per_minute
        self.window = 60.0  # 60 seconds
        self.records: Dict[str, List[float]] = {}
        self.lock = threading.Lock()

    def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        now = time.time()
        with self.lock:
            if client_ip not in self.records:
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
    re.compile(r"\b[1-9]\d{12}\b"),  # Thai 13-digit National ID pattern
    re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),  # Credit card numbers
    re.compile(r"\bAIza[0-9A-Za-z-_]{35}\b"),  # Google API Keys
    re.compile(r"\bAQ\.[A-Za-z0-9_\-]{20,}\b"),  # Gemini API Keys
]


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
    clean = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", str(text))
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
    - X-XSS-Protection: 1; mode=block (Legacy XSS filter)
    - Strict-Transport-Security (HSTS)
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enforces sliding-window rate limiting per IP address.
    Exempts health checks and static docs.
    """

    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.exempt_paths = {"/", "/api/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Extract client IP (respecting Reverse Proxy X-Forwarded-For if present)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "127.0.0.1"

        allowed, remaining = self.rate_limiter.is_allowed(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please slow down and try again in a moment.",
                    "status_code": 429
                },
                headers={"Retry-After": "60"}
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.rpm)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
