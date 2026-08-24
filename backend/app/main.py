from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes_search import router as search_router
from app.api.routes_faculty import router as faculty_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Thesis Advisor & University Matching Engine for Graduate Students in Thailand",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(search_router, prefix="/api/v1")
app.include_router(faculty_router, prefix="/api/v1")


from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", tags=["UI"])
def serve_home_ui():
    """Serve the modern interactive Thai Advisor Match Web Application."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
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
