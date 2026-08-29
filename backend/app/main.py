from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.core.config import settings
from app.api.routes_search import router as search_router
from app.api.routes_faculty import router as faculty_router
from app.api.routes_courses import router as courses_router
from app.api.routes_career_quiz import router as career_quiz_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Thesis Advisor & University Matching Engine for Graduate Students in Thailand",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable GZip Compression for all responses > 1KB (reduces network payload by 70-85%)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Enable CORS for Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(search_router, prefix="/api/v1")
app.include_router(faculty_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")
app.include_router(career_quiz_router, prefix="/api/v1")


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
