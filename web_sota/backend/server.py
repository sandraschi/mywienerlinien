"""My Wiener Linien web_sota backend (fleet-start UvicornTarget: server:app).

Serves the Vite dashboard (port 10896) on backend port 11170.
Fleet-standard endpoints: /api/health, /api/status, /api/skills,
/api/capabilities, /api/v1/diagnostics, POST /api/shutdown,
LLM provider proxy (/api/llm/*), and the activity-log API.
"""

import asyncio
import json
import os
import platform
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import httpx

from web_sota.backend.log_buffer import activity_log
from web_sota.backend.routes.logging import router as logging_router

_HERE = Path(__file__).resolve().parent


def _load_json(name: str):
    try:
        with open(_HERE / name, encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, list) else []
    except Exception:
        return []


MAJOR_STOPS = _load_json("major_stops.json")
LINES_CATALOG = _load_json("lines.json")

WL_BASE = "https://www.wienerlinien.at/ogd_realtime"

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


@app.get("/api/stops/major")
async def stops_major():
    """Curated major-stop table (verified RBLs + GTFS coords, see file header note)."""
    return {"stops": MAJOR_STOPS, "count": len(MAJOR_STOPS)}


@app.get("/api/lines")
async def lines():
    """Line catalog from the Wiener Linien GTFS feed (reference snapshot)."""
    return {"lines": LINES_CATALOG, "count": len(LINES_CATALOG)}


@app.get("/api/departures")
async def departures(rbl: str = Query(..., description="Wiener Linien RBL stop code")):
    """Live departures for one stop via the OGD monitor API (no key needed)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{WL_BASE}/monitor", params={"rbl": rbl})
            resp.raise_for_status()
            payload = resp.json()
    except Exception as e:
        return JSONResponse(status_code=502, content={"rbl": rbl, "departures": [], "error": str(e)})
    out = []
    for mon in payload.get("data", {}).get("monitors", []) or []:
        stop_title = ((mon.get("locationStop") or {}).get("properties") or {}).get("title")
        for line in mon.get("lines", []) or []:
            line_name = line.get("name", "?")
            line_towards = line.get("towards")
            deps = ((line.get("departures") or {}).get("departure") or [])
            if isinstance(deps, dict):
                deps = [deps]
            for dep in deps:
                times = dep.get("departureTime", {}) or {}
                vehicle = dep.get("vehicle", {}) or {}
                out.append({
                    "line": line_name,
                    "destination": vehicle.get("towards") or line_towards or "?",
                    "countdown": times.get("countdown"),
                    "time_planned": times.get("timePlanned"),
                    "time_real": times.get("timeReal"),
                    "platform": dep.get("platform"),
                    "stop": stop_title,
                })
    return {"rbl": rbl, "departures": out, "count": len(out),
            "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/disruptions")
async def disruptions():
    """Live service disruptions via OGD trafficInfoList (no key needed)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{WL_BASE}/trafficInfoList")
            resp.raise_for_status()
            payload = resp.json()
    except Exception as e:
        return JSONResponse(status_code=502, content={"alerts": [], "count": 0, "error": str(e)})
    alerts = []
    for item in payload.get("data", {}).get("trafficInfos", []) or []:
        attrs = item.get("attributes", {}) or {}
        times = item.get("time", {}) or {}
        cat = item.get("refTrafficInfoCategoryId")
        alerts.append({
            "id": str(item.get("name", "")),
            "title": str(item.get("title", "")),
            "description": str(item.get("description", "")),
            "reason": str(attrs.get("reason", "") or ""),
            "lines": [str(x) for x in (attrs.get("relatedLines") or [])],
            "status": str(attrs.get("status", "") or ""),
            "start_time": str(times.get("start", "") or ""),
            "end_time": str(times.get("end", "") or ""),
            "severity": "info" if cat == 1 else "medium",
        })
    return {"alerts": alerts, "count": len(alerts),
            "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/news")
async def news():
    """Live network news/POIs via OGD newsList (no key needed)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{WL_BASE}/newsList")
            resp.raise_for_status()
            payload = resp.json()
    except Exception as e:
        return JSONResponse(status_code=502, content={"pois": [], "count": 0, "error": str(e)})
    pois = payload.get("data", {}).get("pois", []) or []
    items = [{"name": str(p.get("name", "")), "title": str(p.get("title", "")),
              "description": str(p.get("description", ""))} for p in pois]
    return {"pois": items, "count": len(items),
            "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/fleet/apps")
async def fleet_apps():
    """Fleet Apps Hub registry (static; unknown apps belong to Experimental)."""
    return {"apps": [
        {"id": "mywienerlinien", "name": "MyWienerLinien",
         "description": "Vienna transit departures, disruptions, lines + MCP server.",
         "backend_port": 11170, "frontend_port": 10896, "status": "live"},
    ]}


@app.post("/api/chat/stream")
async def chat_stream(body: dict):
    """SSE chat stream proxy (OpenAI-style chunks + [DONE]); falls back to one chunk."""
    provider = body.get("provider", "ollama")
    model = body.get("model", "llama3.2:3b")
    prompt = body.get("prompt") or body.get("message", "")
    base = "http://127.0.0.1:1234/v1" if provider == "lmstudio" else "http://127.0.0.1:11434/v1"

    async def gen():
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", f"{base}/chat/completions", json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                }) as resp:
                    if resp.status_code != 200:
                        yield f'data: {{"error": "Provider HTTP {resp.status_code}"}}\n\n'
                    else:
                        async for line in resp.aiter_lines():
                            if line.startswith("data:"):
                                yield line + "\n\n"
        except Exception as e:
            yield f'data: {{"error": "Error: {e}"}}\n\n'
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


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
