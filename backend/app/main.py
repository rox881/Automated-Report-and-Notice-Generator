from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.connection import init_db
from app.registry.loader import load_all
from app.api.routes import sessions, fields, generate, files

app = FastAPI(title="Report Generator API", version="1.0.0")


@app.on_event("startup")
def startup():
    """Initializes the SQLite DB tables and loads all template registries on start."""
    init_db()
    load_all()


# API routers
app.include_router(sessions.router)
app.include_router(fields.router)
app.include_router(generate.router)
app.include_router(files.router)

# Serve the frontend as static files at root /
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
