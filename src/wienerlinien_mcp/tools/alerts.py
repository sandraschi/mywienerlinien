"""Traffic alerts tool for Vienna Transit MCP."""

from datetime import datetime, timezone
from typing import Optional

import requests
from fastmcp import FastMCP
from pydantic import BaseModel, Field


class TrafficAlert(BaseModel):
    """A traffic disruption or service alert."""

    id: str = Field(..., description="Alert identifier")
    title: str = Field(..., description="Alert title/summary")
    description: str = Field(..., description="Full alert description")
    severity: str = Field(..., description="Severity: low, medium, high")
    category: str = Field(..., description="Category: disruption, construction, event, info")
    affected_lines: list[str] = Field(default_factory=list, description="Affected transit lines")
    affected_stations: list[str] = Field(default_factory=list, description="Affected stations")
    start_time: Optional[datetime] = Field(None, description="When alert started")
    end_time: Optional[datetime] = Field(None, description="Expected end time")
    url: Optional[str] = Field(None, description="Link for more information")


class TrafficAlertsResponse(BaseModel):
    """Response containing current traffic alerts."""

    alerts: list[TrafficAlert] = Field(..., description="Current traffic alerts")
    count: int = Field(..., description="Number of active alerts")
    timestamp: datetime = Field(..., description="When alerts were fetched")
    status: str = Field(..., description="Overall system status")


def register_traffic_alerts_tool(mcp: FastMCP) -> None:
    """Register the traffic_alerts tool with the MCP server."""

    @mcp.tool()
    async def traffic_alerts(
        line_filter: Optional[str] = None,
        severity_filter: Optional[str] = None,
    ) -> TrafficAlertsResponse:
        """Get current traffic disruptions and service alerts.

        Retrieves active alerts about service disruptions, construction work,
        special events, and other issues affecting Vienna public transport.
        Results can be filtered by line or severity.

        Args:
            line_filter: Optional line to filter by (e.g., "U1", "D", "13A")
            severity_filter: Optional severity filter: "low", "medium", "high"

        Returns:
            TrafficAlertsResponse containing:
                - alerts: List of current alerts
                - count: Number of alerts
                - timestamp: When data was fetched
                - status: Overall system status (normal, disrupted, major_issues)

        Example:
            >>> alerts = await traffic_alerts()
            >>> print(f"{alerts.count} active alerts")
            >>> for alert in alerts.alerts:
            ...     print(f"[{alert.severity}] {alert.title}")
        """
        alerts = []

        try:
            # Fetch from Wiener Linien traffic info API
            url = "https://www.wienerlinien.at/ogd_realtime/trafficInfoList"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            traffic_infos = data.get("data", {}).get("trafficInfos", [])

            for info in traffic_infos:
                # Determine severity based on priority or type
                priority = info.get("priority", "").lower()
                if "high" in priority or "störung" in info.get("title", "").lower():
                    severity = "high"
                elif "medium" in priority:
                    severity = "medium"
                else:
                    severity = "low"

                # Apply severity filter
                if severity_filter and severity != severity_filter.lower():
                    continue

                # Extract affected lines
                affected_lines = []
                related_lines = info.get("relatedLines", [])
                for line in related_lines:
                    if isinstance(line, dict):
                        line_name = line.get("name", "")
                    else:
                        line_name = str(line)
                    if line_name:
                        affected_lines.append(line_name)

                # Apply line filter
                if line_filter:
                    if line_filter.upper() not in [line.upper() for line in affected_lines]:
                        continue

                # Extract affected stations
                affected_stations = []
                related_stops = info.get("relatedStops", [])
                for stop in related_stops:
                    if isinstance(stop, dict):
                        stop_name = stop.get("name", "")
                    else:
                        stop_name = str(stop)
                    if stop_name:
                        affected_stations.append(stop_name)

                # Determine category
                info_type = info.get("type", "").lower()
                if "construction" in info_type or "bau" in info.get("title", "").lower():
                    category = "construction"
                elif "event" in info_type or "veranstaltung" in info.get("title", "").lower():
                    category = "event"
                elif "info" in info_type:
                    category = "info"
                else:
                    category = "disruption"

                # Parse times
                start_time = None
                end_time = None
                time_info = info.get("time", {})
                if time_info.get("start"):
                    try:
                        start_time = datetime.fromisoformat(
                            time_info["start"].replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        pass
                if time_info.get("end"):
                    try:
                        end_time = datetime.fromisoformat(time_info["end"].replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass

                alert = TrafficAlert(
                    id=str(info.get("id", "")),
                    title=info.get("title", "Unknown"),
                    description=info.get("description", ""),
                    severity=severity,
                    category=category,
                    affected_lines=affected_lines,
                    affected_stations=affected_stations,
                    start_time=start_time,
                    end_time=end_time,
                    url=info.get("url"),
                )
                alerts.append(alert)

        except requests.RequestException as e:
            # Return empty response with error status if API fails
            return TrafficAlertsResponse(
                alerts=[],
                count=0,
                timestamp=datetime.now(timezone.utc),
                status=f"api_error: {e}",
            )

        # Determine overall status
        high_count = sum(1 for a in alerts if a.severity == "high")
        if high_count >= 3:
            status = "major_issues"
        elif high_count >= 1 or len(alerts) >= 5:
            status = "disrupted"
        else:
            status = "normal"

        return TrafficAlertsResponse(
            alerts=alerts,
            count=len(alerts),
            timestamp=datetime.now(timezone.utc),
            status=status,
        )
