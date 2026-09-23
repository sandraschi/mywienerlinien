"""My Wiener Linien web_sota backend (fleet-start UvicornTarget: server:app).

Serves the Vite dashboard (port 10896) on backend port 11170.
Fleet-standard endpoints: /api/health, /api/status, /api/skills,
/api/capabilities, /api/v1/diagnostics, POST /api/shutdown,
LLM provider proxy (/api/llm/*), and the activity-log API.
"""

import asyncio
import os
import platform
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx

from web_sota.backend.log_buffer import activity_log
from web_sota.backend.routes.logging import router as logging_router

STARTED_AT = time.time()

FRONTEND_PORTS = (os.getenv("FRONTEND_PORTS", "10896,3079,3080")).split(",")
_EXPLICIT_ORIGINS = [
    f"http://localhost:{p.strip()}" for p in FRONTEND_PORTS if p.strip()
] + [
    f"http://127.0.0.1:{p.strip()}" for p in FRONTEND_PORTS if p.strip()
] + [
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
]

# Unconditional regex: loopback + LAN + Tailscale CGNAT + Tauri WebView.
_ORIGIN_REGEX = (
    r"https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+"
    r"|100\.(6\d|[7-9]\d|1\d\d|2[0-6]\d)\.\d+\.\d+|tauri\.localhost)(:\d+)?"
    r"|tauri://localhost"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.activity_log = activity_log
    activity_log.info("server", "Server started")
    yield


app = FastAPI(title="My Wiener Linien", version="2.0.1", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_EXPLICIT_ORIGINS,
    allow_origin_regex=_ORIGIN_REGEX,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(logging_router)


@app.get("/health")
async def health_root():
    return {"status": "ok"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/status")
async def status():
    return {
        "status": "ok",
        "service": "mywienerlinien-webapi",
        "version": "2.0.1",
        "uptime_seconds": round(time.time() - STARTED_AT, 1),
    }


@app.get("/api/skills")
async def skills():
    """Skill-first listing consumed by the Chat UI on mount."""
    return {
        "skills": [
            {
                "name": "vienna-departures",
                "description": "Look up real-time departures for a Vienna stop.",
            },
            {
                "name": "vienna-journey",
                "description": "Plan a route between two Vienna stops.",
            },
            {
                "name": "vienna-disruptions",
                "description": "Check active service disruptions and alerts.",
            },
        ]
    }


@app.get("/api/capabilities")
async def capabilities():
    routes = sorted({r.path for r in app.routes if hasattr(r, "path")})
    return {
        "name": "mywienerlinien",
        "version": "2.0.1",
        "backend_port": int(os.getenv("WEB_PORT", "11170")),
        "endpoints": routes,
        "features": ["llm-proxy", "activity-log", "chat-skills"],
    }


@app.get("/api/v1/diagnostics")
async def diagnostics():
    """CUA-NSIS smoke-test surface: tool list, system info, errors."""
    return {
        "service": "mywienerlinien-webapi",
        "status": "ok",
        "uptime_seconds": round(time.time() - STARTED_AT, 1),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "routes": sorted({r.path for r in app.routes if hasattr(r, "path")}),
        "errors": [],
    }


@app.get("/api/llm/discover")
async def llm_discover():
    return await llm_providers()


@app.get("/api/llm/providers")
async def llm_providers():
    providers = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://127.0.0.1:11434/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                providers.append({"id": "ollama", "label": "Ollama", "base_url": "http://127.0.0.1:11434/v1", "models": models, "needs_key": False})
            else:
                providers.append({"id": "ollama", "label": "Ollama", "base_url": "http://127.0.0.1:11434/v1", "models": [], "needs_key": False})
    except Exception:
        providers.append({"id": "ollama", "label": "Ollama", "base_url": "http://127.0.0.1:11434/v1", "models": [], "needs_key": False})
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://127.0.0.1:1234/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["id"] for m in data.get("data", [])]
                providers.append({"id": "lmstudio", "label": "LM Studio", "base_url": "http://127.0.0.1:1234/v1", "models": models, "needs_key": False})
            else:
                providers.append({"id": "lmstudio", "label": "LM Studio", "base_url": "http://127.0.0.1:1234/v1", "models": [], "needs_key": False})
    except Exception:
        providers.append({"id": "lmstudio", "label": "LM Studio", "base_url": "http://127.0.0.1:1234/v1", "models": [], "needs_key": False})
    return {"providers": providers}


@app.get("/api/llm/models")
async def llm_models():
    info = await llm_providers()
    models = {}
    for p in info.get("providers", []):
        models[p["id"]] = p.get("models", [])
    return {"models": models}


@app.get("/api/llm/onboarding")
async def llm_onboarding():
    return {
        "facts": [
            "Wiener Linien publishes no live vehicle positions; the map shows schedule-interpolated markers.",
            "Departures come from the OGD monitor API per stop RBL.",
            "Incidents come from /trafficInfoList and /newsList.",
        ],
        "recommended_path": "Open Departures, pick a stop, then ask the chat for disruptions on your line.",
    }


@app.post("/api/llm/chat")
async def llm_chat(body: dict):
    provider = body.get("provider", "ollama")
    model = body.get("model", "llama3.2:3b")
    prompt = body.get("prompt") or body.get("message", "")
    base = "http://127.0.0.1:1234/v1" if provider == "lmstudio" else "http://127.0.0.1:11434/v1"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{base}/chat/completions", json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            })
            if resp.status_code == 200:
                data = resp.json()
                return {"response": data["choices"][0]["message"]["content"]}
            return JSONResponse(status_code=502, content={"response": f"Provider HTTP {resp.status_code}"})
    except Exception as e:
        return JSONResponse(status_code=502, content={"response": f"Error: {e}"})


@app.post("/api/shutdown")
async def shutdown():
    """Orderly exit for the fleet launcher: 200 now, exit after 500 ms."""

    async def _exit_later():
        await asyncio.sleep(0.5)
        os._exit(0)

    asyncio.create_task(_exit_later())
    return {"success": True, "message": "Shutting down in 500 ms."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("WEB_PORT", "11170")))
