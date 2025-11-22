"""Pydantic models for station search MCP tools."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Station(BaseModel):
    """Station information."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Stephansplatz",
                "rbl": "60201368",
                "type": "metro",
                "zone": "100",
                "lat": 48.2082,
                "lng": 16.3738
            }
        }
    )
    
    name: str = Field(..., description="Station name")
    rbl: Optional[str] = Field(None, description="Station RBL code (Vienna-specific)")
    type: str = Field(..., description="Station type (metro, tram, bus)")
    zone: Optional[str] = Field(None, description="Fare zone")
    lat: Optional[float] = Field(None, description="Latitude")
    lng: Optional[float] = Field(None, description="Longitude")


class StationSearchResponse(BaseModel):
    """Response containing search results for stations."""
    
    query: str = Field(..., description="Original search query")
    results: List[Station] = Field(..., description="Matching stations")
    count: int = Field(..., description="Number of results")

