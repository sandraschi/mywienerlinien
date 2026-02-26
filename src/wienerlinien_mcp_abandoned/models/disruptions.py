"""Pydantic models for disruption-related MCP tools."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Disruption(BaseModel):
    """Disruption information with structured schema."""

    id: str = Field(..., description="Unique disruption identifier")
    title: str = Field(..., description="Disruption title/headline")
    description: str = Field(..., description="Detailed description of the disruption")
    line: Optional[str] = Field(None, description="Affected line (if specific)")
    type: str = Field(..., description="Disruption type (delay, cancellation, detour, closure, technical, maintenance, weather, accident, other)")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    status: str = Field(..., description="Current status (active, resolved, scheduled, cancelled)")
    affected_stations: List[str] = Field(default_factory=list, description="Stations affected by this disruption")
    affected_lines: List[str] = Field(default_factory=list, description="Lines affected by this disruption")
    start_time: Optional[datetime] = Field(None, description="When the disruption started")
    end_time: Optional[datetime] = Field(None, description="When the disruption is expected to end")
    created_at: datetime = Field(..., description="When this disruption was first reported")
    updated_at: datetime = Field(..., description="When this disruption was last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "disruption_123",
                "title": "Signal failure at Karlsplatz",
                "description": "Technical issues with signaling system causing delays",
                "line": "U1",
                "type": "technical",
                "severity": "high",
                "status": "active",
                "affected_stations": ["Karlsplatz", "Stephansplatz"],
                "affected_lines": ["U1"],
                "start_time": "2025-01-15T10:30:00Z",
                "end_time": "2025-01-15T12:00:00Z",
                "created_at": "2025-01-15T10:25:00Z",
                "updated_at": "2025-01-15T10:45:00Z",
            }
        }


class DisruptionResponse(BaseModel):
    """Response containing list of disruptions."""

    disruptions: List[Disruption] = Field(..., description="List of disruptions")
    count: int = Field(..., description="Total number of disruptions returned")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class DisruptionSummaryResponse(BaseModel):
    """Response containing disruption summary statistics."""

    total_active: int = Field(..., description="Total number of active disruptions")
    by_severity: dict = Field(..., description="Count of disruptions by severity level")
    by_type: dict = Field(..., description="Count of disruptions by type")
    most_affected_lines: List[dict] = Field(..., description="Lines most affected by disruptions")
    last_updated: datetime = Field(..., description="When this summary was last updated")