from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.core.config import settings
from app.core.security import SecurityHeadersMiddleware, RateLimitMiddleware, RateLimiter
from app.api.routes_search import router as search_router
from app.api.routes_faculty import router as faculty_router
from app.api.routes_courses import router as courses_router
from app.api.routes_career_quiz import router as career_quiz_router
from app.api.routes_universities import router as universities_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Thesis Advisor & University Matching Engine for Graduate Students in Thailand",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. Security Headers (OWASP Hardening)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Rate Limiting (180 requests per minute per IP to prevent DoS & scraping abuse)
rate_limiter = RateLimiter(requests_per_minute=180)
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

# 3. Enable GZip Compression for all responses > 1KB (reduces network payload by 70-85%)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 4. Restrict CORS to authorized origins (Frontend local & production domains)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https://.*\.vercel\.app$|^https://.*\.render\.com$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
    max_age=600,
)

# Register API Routers
app.include_router(search_router, prefix="/api/v1")
app.include_router(faculty_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")
app.include_router(career_quiz_router, prefix="/api/v1")
app.include_router(universities_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root():
    """Root endpoint for API status."""
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
