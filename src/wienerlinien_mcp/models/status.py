"""Pydantic models for service status MCP tools."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    """Service status information for a line or system."""
    
    line: Optional[str] = Field(None, description="Line name (null for system-wide status)")
    status: str = Field(..., description="Status (operational, disrupted, delayed)")
    severity: str = Field(..., description="Severity level (low, medium, high)")
    title: str = Field(..., description="Status title")
    description: str = Field(..., description="Detailed description")
    affected_stations: List[str] = Field(default_factory=list, description="Affected stations")
    start_time: Optional[datetime] = Field(None, description="Start time of disruption")
    end_time: Optional[datetime] = Field(None, description="Expected end time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "line": "U1",
                "status": "disrupted",
                "severity": "medium",
                "title": "Service Disruption",
                "description": "Delays due to signal problems",
                "affected_stations": ["Stephansplatz", "Praterstern"],
                "start_time": "2025-01-15T14:00:00Z",
                "end_time": None
            }
        }


class LineStatusResponse(BaseModel):
    """Response containing service status information."""
    
    line_filter: Optional[str] = Field(None, description="Filtered line (null if all lines)")
    statuses: List[ServiceStatus] = Field(..., description="List of status entries")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

