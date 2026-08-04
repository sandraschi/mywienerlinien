"""Socket.IO management for the FastAPI application."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import socketio

try:
    from .disruption_alerts import disruption_monitor
    from .vehicle_service import collect_vehicle_data, get_vehicle_summary
except ImportError:  # pragma: no cover - runtime fallback when package context missing
    from disruption_alerts import disruption_monitor  # type: ignore
    from vehicle_service import collect_vehicle_data, get_vehicle_summary  # type: ignore

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Bridge between python-socketio and application state."""

    def __init__(self, sio: socketio.AsyncServer) -> None:
        self.sio = sio
        self.connected_clients: dict[str, dict[str, Any]] = {}
        self._running = False
        self._background_task: asyncio.Task[None] | None = None
        self._vehicle_snapshot_count = 0
        self._vehicle_total_count = 0
        self._register_handlers()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._background_task = self.sio.start_background_task(self._broadcast_loop)
        logger.info("WebSocket manager started")

    def stop(self) -> None:
        self._running = False
        if self._background_task and not self._background_task.done():
            self._background_task.cancel()
        logger.info("WebSocket manager stopped")

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    def get_connected_clients_count(self) -> int:
        return len(self.connected_clients)

    def get_vehicle_count(self) -> int:
        return self._vehicle_snapshot_count

    def get_vehicle_total_count(self) -> int:
        return self._vehicle_total_count

    def get_filters_summary(self) -> dict[str, int]:
        summary = {
            "clients": len(self.connected_clients),
            "line_filters": 0,
            "type_filters": 0,
        }

        for metadata in self.connected_clients.values():
            filters = metadata.get("filters", {})
            if filters.get("lines"):
                summary["line_filters"] += 1
            vehicle_type = filters.get("vehicle_type")
            if vehicle_type and vehicle_type != "all":
                summary["type_filters"] += 1

        return summary

    # ------------------------------------------------------------------
    # Socket.IO event wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        @self.sio.event
        async def connect(sid: str, environ: dict[str, Any], auth: Any) -> bool:
            self.connected_clients[sid] = {
                "connected_at": datetime.utcnow(),
                "filters": {"vehicle_type": "all", "lines": set()},
            }
            logger.info("Client connected: %s", sid)
            await self.sio.emit(
                "connected",
                {"client_id": sid, "timestamp": datetime.utcnow().isoformat()},
                to=sid,
            )
            return True

        @self.sio.event
        async def disconnect(sid: str) -> None:
            self.connected_clients.pop(sid, None)
            logger.info("Client disconnected: %s", sid)

        @self.sio.on("join_room")
        async def join_room_event(sid: str, data: dict[str, Any]) -> None:
            room = data.get("room") if isinstance(data, dict) else None
            if room:
                await self.sio.enter_room(sid, room)
                logger.info("Client %s joined room %s", sid, room)

        @self.sio.on("leave_room")
        async def leave_room_event(sid: str, data: dict[str, Any]) -> None:
            room = data.get("room") if isinstance(data, dict) else None
            if room:
                await self.sio.leave_room(sid, room)
                logger.info("Client %s left room %s", sid, room)

        @self.sio.on("request_updates")
        async def request_updates_event(sid: str, data: dict[str, Any]) -> None:
            update_type = data.get("type") if isinstance(data, dict) else "all"

            if update_type in {"vehicles", "all"}:
                await self._send_vehicle_updates(sid)
            if update_type in {"disruptions", "all"}:
                await self._send_disruptions(sid)
            if update_type in {"status", "all"}:
                await self._send_status(sid)

        @self.sio.on("update_filters")
        async def update_filters_event(sid: str, data: dict[str, Any]) -> None:
            filters = self.connected_clients.setdefault(
                sid,
                {
                    "connected_at": datetime.utcnow(),
                    "filters": {"vehicle_type": "all", "lines": set()},
                },
            )["filters"]

            if isinstance(data, dict):
                vehicle_type = data.get("vehicle_type")
                if isinstance(vehicle_type, str) and vehicle_type.strip():
                    filters["vehicle_type"] = vehicle_type.strip().lower()

                lines_payload = data.get("lines")
                if isinstance(lines_payload, list):
                    normalized_lines = {
                        str(item).strip().upper()
                        for item in lines_payload
                        if isinstance(item, (str, int)) and str(item).strip()
                    }
                    filters["lines"] = normalized_lines

            logger.debug(
                "Updated filters for %s: type=%s lines=%s",
                sid,
                filters.get("vehicle_type"),
                sorted(filters.get("lines", [])),
            )
            await self._send_vehicle_updates(sid)

    # ------------------------------------------------------------------
    # Broadcast helpers
    # ------------------------------------------------------------------

    async def _broadcast_loop(self) -> None:
        while self._running:
            try:
                await self._send_vehicle_updates()
                await self._send_status()
                await self._send_disruptions()
            except asyncio.CancelledError:  # pragma: no cover - shutdown path
                raise
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Error in websocket broadcast loop: %s", exc, exc_info=True)
            await asyncio.sleep(30)

    async def _send_vehicle_updates(self, sid: str | None = None) -> None:
        if sid:
            client = self.connected_clients.get(sid, {})
            filters = client.get("filters", {}) if client else {}
            requested_lines = (
                sorted(filters.get("lines") or [])
                if isinstance(filters.get("lines"), (set, list))
                else None
            )
        else:
            aggregated: set[str] = set()
            for metadata in self.connected_clients.values():
                lines_filter = metadata.get("filters", {}).get("lines")
                if isinstance(lines_filter, (set, list)):
                    aggregated.update({str(item).strip().upper() for item in lines_filter if item})
            requested_lines = sorted(aggregated) if aggregated else None

        snapshot = await asyncio.to_thread(collect_vehicle_data, lines=requested_lines)
        vehicles = snapshot["vehicles"]
        total_vehicles = len(vehicles)
        self._vehicle_snapshot_count = total_vehicles
        self._vehicle_total_count = total_vehicles

        targets: list[str]
        if sid:
            targets = [sid]
        else:
            targets = list(self.connected_clients.keys())

        for target_sid in targets:
            client = self.connected_clients.get(target_sid)
            if not client:
                continue
            filters = client.get("filters", {"vehicle_type": "all", "lines": set()})
            filtered = self._apply_filters(vehicles, filters)
            client["last_vehicle_count"] = len(filtered)
            payload = {
                "vehicles": filtered,
                "timestamp": datetime.utcnow().isoformat(),
                "total": total_vehicles,
                "count": len(filtered),
            }
            await self.sio.emit("vehicle_updates", payload, to=target_sid)
            logger.debug(
                "Vehicle update dispatched",
                extra={
                    "sid": target_sid,
                    "requested_lines": sorted(filters.get("lines", [])) if filters else None,
                    "vehicle_type": filters.get("vehicle_type"),
                    "filtered_count": payload["count"],
                    "total_available": total_vehicles,
                },
            )

    async def _send_disruptions(self, sid: str | None = None) -> None:
        disruptions = disruption_monitor.get_active_disruptions()
        disruption_payload = [
            {
                "id": disruption.id,
                "line": disruption.line,
                "type": disruption.type.value,
                "severity": disruption.severity.value,
                "title": disruption.title,
                "description": disruption.description,
                "start_time": disruption.start_time.isoformat(),
                "created_at": disruption.created_at.isoformat(),
            }
            for disruption in disruptions
        ]
        await self.sio.emit(
            "disruption_alerts",
            {"alerts": disruption_payload, "timestamp": datetime.utcnow().isoformat()},
            to=sid,
        )

    async def _send_status(self, sid: str | None = None) -> None:
        vehicle_summary = get_vehicle_summary()
        self._vehicle_snapshot_count = vehicle_summary.get("vehicles_total", 0)
        self._vehicle_total_count = vehicle_summary.get("vehicles_total", 0)

        payload = {
            "websocket_clients": self.get_connected_clients_count(),
            "vehicle_count": self._vehicle_snapshot_count,
            "vehicle_total": self._vehicle_total_count,
            "filters": self.get_filters_summary(),
            "vehicle_updated_at": vehicle_summary.get("generated_at"),
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.sio.emit("system_status", payload, to=sid)

    @staticmethod
    def _apply_filters(
        vehicles: list[dict[str, Any]], filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if not vehicles:
            return []

        filtered = vehicles

        vehicle_type = (filters or {}).get("vehicle_type")
        if isinstance(vehicle_type, str) and vehicle_type and vehicle_type.lower() != "all":
            filtered = [
                vehicle
                for vehicle in filtered
                if vehicle.get("type", "").lower() == vehicle_type.lower()
            ]

        line_filters = (filters or {}).get("lines")
        if line_filters:
            normalized_lines = {str(line).upper() for line in line_filters}
            filtered = [
                vehicle
                for vehicle in filtered
                if vehicle.get("line", "").upper() in normalized_lines
            ]

        return filtered


_manager: WebSocketManager | None = None


def init_websocket_manager(sio: socketio.AsyncServer) -> WebSocketManager:
    global _manager
    if _manager is None:
        _manager = WebSocketManager(sio)
    return _manager


def get_websocket_manager() -> WebSocketManager | None:
    return _manager


__all__ = ["WebSocketManager", "init_websocket_manager", "get_websocket_manager"]
