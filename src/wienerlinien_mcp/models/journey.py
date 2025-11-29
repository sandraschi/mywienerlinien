"""Pydantic models for journey planning MCP tools."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class JourneySegment(BaseModel):
    """A segment of a journey (e.g., one leg with transfers)."""
    
    line: str = Field(..., description="Line name")
    from_station: str = Field(..., description="Origin station")
    to_station: str = Field(..., description="Destination station")
    departure_time: datetime = Field(..., description="Departure time")
    arrival_time: datetime = Field(..., description="Arrival time")
    duration_minutes: int = Field(..., description="Duration in minutes")
    vehicle_type: str = Field(..., description="Vehicle type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "line": "U1",
                "from_station": "Stephansplatz",
                "to_station": "Praterstern",
                "departure_time": "2025-01-15T14:30:00Z",
                "arrival_time": "2025-01-15T14:45:00Z",
                "duration_minutes": 15,
                "vehicle_type": "metro"
            }
        }


class JourneyPlan(BaseModel):
    """Complete journey plan between two stations."""
    
    from_station: str = Field(..., description="Origin station name")
    to_station: str = Field(..., description="Destination station name")
    departure_time: datetime = Field(..., description="Requested departure time")
    total_duration_minutes: int = Field(..., description="Total journey duration in minutes")
    segments: List[JourneySegment] = Field(..., description="Journey segments")
    transfers: int = Field(..., description="Number of transfers required")
    estimated_cost: Optional[str] = Field(None, description="Estimated fare cost")
    
    class Config:
        json_schema_extra = {
            "example": {
                "from_station": "Stephansplatz",
                "to_station": "Praterstern",
                "departure_time": "2025-01-15T14:30:00Z",
                "total_duration_minutes": 15,
                "segments": [],
                "transfers": 0,
                "estimated_cost": "€2.40"
            }
        }



