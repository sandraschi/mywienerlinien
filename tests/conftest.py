"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import importlib
import os
import sys
import types

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("WIENER_LINIEN_TEST_MODE", "1")


def _ensure_socketio_stub() -> None:
    if "socketio" in sys.modules:
        return

    stub = types.ModuleType("socketio")

    class _DummyTask:
        def done(self) -> bool:
            return True

        def cancel(self) -> None:
            pass

    class AsyncServer:  # pragma: no cover - test stub
        def __init__(self, *args, **kwargs):
            pass

        def event(self, func):
            return func

        def on(self, _event):
            def decorator(func):
                return func

            return decorator

        async def emit(self, *args, **kwargs):
            return None

        async def enter_room(self, *args, **kwargs):
            return None

        async def leave_room(self, *args, **kwargs):
            return None

        def start_background_task(self, _coro):
            return _DummyTask()

    class ASGIApp:  # pragma: no cover - test stub
        def __init__(self, _server, other_asgi_app=None, socketio_path="/socket.io"):
            self.other_asgi_app = other_asgi_app

        async def __call__(self, scope, receive, send):
            if self.other_asgi_app is not None:
                await self.other_asgi_app(scope, receive, send)

    stub.AsyncServer = AsyncServer
    stub.ASGIApp = ASGIApp
    sys.modules["socketio"] = stub


_ensure_socketio_stub()


@pytest.fixture(scope="session")
def app_module():
    """Import the FastAPI application module once per test session."""

    return importlib.import_module("frontend.app")


@pytest.fixture()
def app_client(app_module):
    """Yield a FastAPI TestClient instance."""

    client = TestClient(app_module.fastapi_app)
    with client:
        yield client
