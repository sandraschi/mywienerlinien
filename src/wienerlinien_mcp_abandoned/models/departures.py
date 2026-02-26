"""Pydantic models for departure-related MCP tools."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Departure(BaseModel):
    """Departure information with structured schema."""

    line: str = Field(..., description="Line name (e.g., U1, D, 13A)")
    destination: str = Field(..., description="Destination station name")
    departure_time: datetime = Field(..., description="Scheduled departure time")
    countdown_minutes: int = Field(..., description="Minutes until departure")
    delay_minutes: Optional[int] = Field(None, description="Delay in minutes (null if on time)")
    platform: Optional[str] = Field(None, description="Platform number or track")
    vehicle_type: str = Field(..., description="Vehicle type (metro, tram, bus, nightbus)")

    class Config:
        json_schema_extra = {
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


class DepartureResponse(BaseModel):
    """Response containing list of departures."""

    station_name: str = Field(..., description="Station name")
    station_rbl: Optional[str] = Field(None, description="Station RBL code")
    departures: List[Departure] = Field(..., description="List of upcoming departures")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class TimetableEntry(BaseModel):
    """Single timetable entry."""

    time: str = Field(..., description="Departure time in HH:MM format")
    direction: str = Field(..., description="Trip direction/destination")


class TimetableLine(BaseModel):
    """Timetable for a specific line."""

    line: str = Field(..., description="Line name")
    vehicle_type: str = Field(..., description="Vehicle type")
    departures: List[TimetableEntry] = Field(..., description="Scheduled departures")


class TimetableResponse(BaseModel):
    """Response containing station timetable."""

    station: str = Field(..., description="Station name")
    lines: List[TimetableLine] = Field(..., description="Timetable for each line")
    time_window: str = Field(..., description="Time window covered (e.g., '06:00 +1h')")
