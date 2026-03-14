"""
Main FastAPI application for Wall Finishing Robot Control System.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from .core.config import settings
from .core.logging import logger, RequestLoggingMiddleware
from .db.database import init_db, close_db
from .api.trajectories import router as trajectory_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Wall Finishing Robot Control System...")
    await init_db()
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Application stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(trajectory_router)

# Mount static files
app.mount("/static", StaticFiles(directory="backend/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main frontend page."""
    try:
        with open("backend/templates/index.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <head><title>Wall Finishing Robot</title></head>
            <body>
                <h1>Wall Finishing Robot Control System</h1>
                <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
            </body>
        </html>
        """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "service": "Wall Finishing Robot Control System"
    }
