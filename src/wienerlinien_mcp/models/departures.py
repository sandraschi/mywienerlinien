"""Pydantic models for departure-related MCP tools."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Departure(BaseModel):
    """Departure information with structured schema."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "line": "U1",
                "destination": "Leopoldau",
                "departure_time": "2025-01-15T14:30:00Z",
                "countdown_minutes": 3,
                "delay_minutes": 0,
                "platform": "1",
                "vehicle_type": "metro",
            }
        }
    )

    line: str = Field(..., description="Line name (e.g., U1, D, 13A)")
    destination: str = Field(..., description="Destination station name")
    departure_time: datetime = Field(..., description="Scheduled departure time")
    countdown_minutes: int = Field(..., description="Minutes until departure")
    delay_minutes: Optional[int] = Field(None, description="Delay in minutes (null if on time)")
    platform: Optional[str] = Field(None, description="Platform number or track")
    vehicle_type: str = Field(..., description="Vehicle type (metro, tram, bus, nightbus)")


class DepartureResponse(BaseModel):
    """Response containing list of departures."""

    station_name: str = Field(..., description="Station name")
    station_rbl: Optional[str] = Field(None, description="Station RBL code")
    departures: list[Departure] = Field(..., description="List of upcoming departures")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
