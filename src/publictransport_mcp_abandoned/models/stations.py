"""Pydantic models for station search MCP tools."""

from pydantic import BaseModel, Field


class Station(BaseModel):
    """Station information."""

    name: str = Field(..., description="Station name")
    rbl: str | None = Field(None, description="Station RBL code (Vienna-specific)")
    type: str = Field(..., description="Station type (metro, tram, bus)")
    zone: str | None = Field(None, description="Fare zone")
    lat: float | None = Field(None, description="Latitude")
    lng: float | None = Field(None, description="Longitude")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Stephansplatz",
                "rbl": "60201368",
                "type": "metro",
                "zone": "100",
                "lat": 48.2082,
                "lng": 16.3738,
            }
        }


class StationSearchResponse(BaseModel):
    """Response containing search results for stations."""

    query: str = Field(..., description="Original search query")
    results: list[Station] = Field(..., description="Matching stations")
    count: int = Field(..., description="Number of results")
