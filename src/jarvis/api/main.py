"""FastAPI application for JARVIS."""
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, func, select

from jarvis.api.auth import require_viewer
from jarvis.api.routes import agents, auth, cycles, health, instruments, news, signals, stats
from jarvis.api.sse import sse_endpoint, sse_manager
from jarvis.db.models import UserModel
from jarvis.db.session import make_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting JARVIS API...")
    # Initialize default user if none exists
    engine = make_engine()
    with Session(engine) as session:
        user_count = session.exec(select(func.count(UserModel.id))).first() or 0
        if user_count == 0:
            # Create default owner from env or use default
            import os

            from jarvis.api.auth import hash_password
            default_user = os.getenv("DEFAULT_USER", "admin")
            default_pass = os.getenv("DEFAULT_PASS", "changeme")
            default_role = os.getenv("DEFAULT_ROLE", "OWNER")
            user = UserModel(
                id=datetime.now(UTC).isoformat().replace(":", "").replace("-", "")[:24],
                username=default_user,
                password_hash=hash_password(default_pass),
                role=default_role,
                active=1,
                created_at=datetime.now(UTC),
            )
            session.add(user)
            session.commit()
            print(f"Created default user: {default_user}")
    yield
    # Shutdown
    print("Shutting down JARVIS API...")


app = FastAPI(
    title="JARVIS API",
    version="0.1.0",
    description="Multi-Agent Trade Signal Intelligence API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS - restrict to dashboard origin in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    request_id = datetime.now(UTC).isoformat().replace(":", "").replace("-", "")[:24]
    print(f"[{request_id}] Unhandled error: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL",
                "message": "Internal server error",
                "request_id": request_id,
            }
        },
    )


# Include routes
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(signals.router, prefix="/api/v1")
app.include_router(instruments.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(cycles.router, prefix="/api/v1")
app.include_router(news.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")


# SSE endpoint
@app.get("/api/v1/stream")
async def sse_stream(request: Request, current_user=Depends(require_viewer)):  # noqa: B008
    """SSE endpoint for real-time updates."""
    return await sse_endpoint(request)


# Dev: SSE test endpoint
@app.post("/api/v1/dev/sse/test")
async def sse_test(request: Request):
    """Test SSE broadcast."""
    data = await request.json()
    await sse_manager.broadcast(data.get("type", "test"), data.get("data", {}))
    return {"status": "broadcast sent"}


# Serve built frontend (if exists) - mount static assets and catch-all for SPA
web_dist = Path(__file__).resolve().parents[3] / "web" / "dist"
if web_dist.exists():
    # Mount static assets (JS, CSS, images) under /assets
    assets_dir = web_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    # Mount other static files (favicon, icons)
    app.mount("/favicon.svg", StaticFiles(directory=web_dist), name="favicon")
    app.mount("/icons.svg", StaticFiles(directory=web_dist), name="icons")
    
    # Catch-all route for SPA - serve index.html for non-API routes
    @app.get("/{full_path:path}")
    async def spa_catchall(full_path: str):
        print(f"[SPA] Request: {full_path}")
        # Only serve index.html for non-API paths
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi"):
            print(f"[SPA] API path, returning 404")
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        index_file = web_dist / "index.html"
        if index_file.exists():
            print(f"[SPA] Serving index.html")
            return FileResponse(index_file)
        print(f"[SPA] Frontend not built")
        return JSONResponse(status_code=404, content={"detail": "Frontend not built"})
@app.get("/api/v1/stream")
async def sse_stream(request: Request, current_user=Depends(require_viewer)):  # noqa: B008
    """SSE endpoint for real-time updates."""
    return await sse_endpoint(request)


# Dev: SSE test endpoint
@app.post("/api/v1/dev/sse/test")
async def sse_test(request: Request):
    """Test SSE broadcast."""
    data = await request.json()
    await sse_manager.broadcast(data.get("type", "test"), data.get("data", {}))
    return {"status": "broadcast sent"}