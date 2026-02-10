"""
Verkeersboete AI Agent - Main Application

An autonomous AI agent that processes Dutch traffic fines (CJIB beschikkingen),
performs legal analysis under the Wet Mulder (Wahv), and generates
bezwaarschriften (appeal documents).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import settings
from app.database import Base, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Verkeersboete AI Agent...")
    settings.ensure_dirs()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")
    yield
    # Shutdown
    logger.info("Shutting down Verkeersboete AI Agent.")


app = FastAPI(
    title="Verkeersboete AI Agent",
    description=(
        "Autonome AI-agent voor het analyseren van verkeersboetes en "
        "genereren van bezwaarschriften op basis van de Wet Mulder (Wahv)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": "Verkeersboete AI Agent",
        "version": "1.0.0",
        "description": "Upload een verkeersboete en ontvang een automatisch bezwaarschrift.",
        "docs": "/docs",
    }
