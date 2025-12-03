"""Stop timetable tool for Vienna Transit MCP."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field


def _load_calendar_services(day_type: str) -> set[str]:
    """Load service_ids that run on the specified day type from calendar.txt.

    Args:
        day_type: One of 'weekday', 'saturday', 'sunday'

    Returns:
        Set of service_ids that run on that day type
    """
    # Find the calendar.txt file
    gtfs_paths = [
        Path(__file__).parent.parent.parent.parent
        / "scripts"
        / "gtfs_data"
        / "extracted"
        / "calendar.txt",
        Path("scripts/gtfs_data/extracted/calendar.txt"),
        Path("D:/Dev/repos/mywienerlinien/scripts/gtfs_data/extracted/calendar.txt"),
    ]

    calendar_path = None
    for p in gtfs_paths:
        if p.exists():
            calendar_path = p
            break

    if not calendar_path:
        return set()  # No calendar file, return empty (will show all services)

    # Map day_type to column names
    day_columns = {
        "weekday": ["monday", "tuesday", "wednesday", "thursday", "friday"],
        "saturday": ["saturday"],
        "sunday": ["sunday"],
    }

    columns = day_columns.get(day_type.lower(), day_columns["weekday"])
    valid_services = set()

    try:
        with open(calendar_path, encoding="utf-8-sig") as f:  # utf-8-sig handles BOM
            reader = csv.DictReader(f)
            for row in reader:
                # Check if service runs on any of the required days
                runs_on_day = any(row.get(col, "0") == "1" for col in columns)
                if runs_on_day:
                    service_id = row.get("service_id", "")
                    if service_id:
                        valid_services.add(service_id)
    except Exception as e:
        import logging

        logging.getLogger("timetable").warning(f"Calendar load failed: {e}")
        return set()  # On error, return empty (will show all services)

    return valid_services


class TimetableEntry(BaseModel):
    """A single departure time in the timetable."""

    time: str = Field(..., description="Departure time (HH:MM)")
    line: str = Field(..., description="Line identifier")
    direction: str = Field(..., description="Direction/headsign")
    trip_id: str = Field(..., description="Trip identifier for reference")


class TimetableHour(BaseModel):
    """Departures grouped by hour."""

    hour: int = Field(..., description="Hour (0-23)")
    hour_label: str = Field(..., description="Hour display (e.g., '06:00')")
    departures: list[TimetableEntry] = Field(..., description="Departures in this hour")
    count: int = Field(..., description="Number of departures in this hour")


class StopTimetableResponse(BaseModel):
    """Complete timetable for a stop."""

    stop_name: str = Field(..., description="Stop name")
    stop_id: str = Field(..., description="Stop identifier")
    line_filter: Optional[str] = Field(None, description="Line filter applied")
    day_type: str = Field(..., description="Day type: weekday, saturday, sunday")
    service_date: str = Field(..., description="Reference date for schedule")
    hours: list[TimetableHour] = Field(..., description="Departures by hour")
    total_departures: int = Field(..., description="Total departures in timetable")
    first_departure: Optional[str] = Field(None, description="First departure time")
    last_departure: Optional[str] = Field(None, description="Last departure time")
    lines_serving: list[str] = Field(..., description="All lines serving this stop")
    html: Optional[str] = Field(None, description="HTML formatted timetable")


def _generate_html_timetable(response: "StopTimetableResponse") -> str:
    """Generate HTML formatted timetable."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Timetable: {response.stop_name}</title>
    <style>
        :root {{
            --primary: #e20210;
            --secondary: #1a1a2e;
            --bg: #0f0f1a;
            --card-bg: #1a1a2e;
            --text: #e8e8e8;
            --muted: #888;
            --metro: #0066cc;
            --tram: #cc0000;
            --bus: #009933;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg);
            color: var(--text);
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, var(--primary), #ff4444);
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 24px;
        }}
        .header h1 {{ font-size: 1.8em; margin-bottom: 8px; }}
        .header .meta {{ color: rgba(255,255,255,0.8); font-size: 0.9em; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .summary-card {{
            background: var(--card-bg);
            padding: 16px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card .value {{ font-size: 1.5em; font-weight: bold; color: var(--primary); }}
        .summary-card .label {{ font-size: 0.85em; color: var(--muted); }}
        .timetable {{
            background: var(--card-bg);
            border-radius: 12px;
            overflow: hidden;
        }}
        .hour-row {{
            display: flex;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .hour-row:last-child {{ border-bottom: none; }}
        .hour-label {{
            width: 80px;
            min-width: 80px;
            padding: 16px;
            background: rgba(226,2,16,0.1);
            font-weight: bold;
            font-size: 1.1em;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .departures {{
            flex: 1;
            padding: 12px 16px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
        }}
        .departure {{
            background: rgba(255,255,255,0.1);
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 0.9em;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .departure .minute {{ font-weight: bold; }}
        .departure .line {{
            font-size: 0.75em;
            padding: 2px 6px;
            border-radius: 3px;
            background: var(--metro);
        }}
        .departure .line.tram {{ background: var(--tram); }}
        .departure .line.bus {{ background: var(--bus); }}
        .no-service {{
            color: var(--muted);
            font-style: italic;
            padding: 8px;
        }}
        .lines-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 16px;
        }}
        .line-badge {{
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        .line-badge.U {{ background: #0066cc; }}
        .line-badge.tram {{ background: #cc0000; }}
        .line-badge.bus {{ background: #009933; }}
        @media (max-width: 600px) {{
            .hour-label {{ width: 60px; min-width: 60px; font-size: 1em; }}
            .departure {{ padding: 4px 8px; font-size: 0.85em; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚇 {response.stop_name}</h1>
        <div class="meta">
            {response.day_type.title()} Schedule | {response.service_date}
            {f" | Line: {response.line_filter}" if response.line_filter else ""}
        </div>
    </div>

    <div class="summary">
        <div class="summary-card">
            <div class="value">{response.total_departures}</div>
            <div class="label">Total Departures</div>
        </div>
        <div class="summary-card">
            <div class="value">{response.first_departure or "--"}</div>
            <div class="label">First Service</div>
        </div>
        <div class="summary-card">
            <div class="value">{response.last_departure or "--"}</div>
            <div class="label">Last Service</div>
        </div>
        <div class="summary-card">
            <div class="value">{len(response.lines_serving)}</div>
            <div class="label">Lines</div>
        </div>
    </div>

    <div class="lines-legend">
"""
    # Add line badges
    for line in sorted(response.lines_serving):
        line_class = (
            "U"
            if line.startswith("U")
            else ("tram" if line.isdigit() or line in ["D", "O"] else "bus")
        )
        html += f'        <span class="line-badge {line_class}">{line}</span>\n'

    html += """    </div>

    <div class="timetable">
"""
    # Add hour rows
    for hour_data in response.hours:
        html += f"""        <div class="hour-row">
            <div class="hour-label">{hour_data.hour_label}</div>
            <div class="departures">
"""
        if hour_data.departures:
            for dep in hour_data.departures:
                minute = dep.time.split(":")[1]
                line_class = (
                    "U"
                    if dep.line.startswith("U")
                    else ("tram" if dep.line.isdigit() or dep.line in ["D", "O"] else "bus")
                )
                html += f'                <span class="departure"><span class="line {line_class}">{dep.line}</span><span class="minute">:{minute}</span></span>\n'
        else:
            html += '                <span class="no-service">No service</span>\n'

        html += """            </div>
        </div>
"""

    html += """    </div>
</body>
</html>"""
    return html


def register_stop_timetable_tool(mcp: FastMCP) -> None:
    """Register the stop_timetable tool with the MCP server."""

    @mcp.tool()
    async def stop_timetable(
        stop: str,
        line: Optional[str] = None,
        day_type: str = "weekday",
        include_html: bool = True,
    ) -> StopTimetableResponse:
        """Get the full daily timetable for a stop.

        Shows all scheduled departures throughout the day, grouped by hour.
        Useful for understanding service patterns, first/last trains, and
        frequency at different times.

        Args:
            stop: Stop name to get timetable for (fuzzy matching supported)
            line: Optional line filter (e.g., "U4", "13A"). Default shows all lines.
            day_type: Schedule type - "weekday", "saturday", or "sunday"
            include_html: Include HTML formatted timetable for display (default True)

        Returns:
            StopTimetableResponse containing:
                - stop_name: Resolved stop name
                - day_type: Schedule type used
                - hours: Departures grouped by hour (0-23)
                - total_departures: Total count
                - first_departure/last_departure: Service span
                - lines_serving: All lines at this stop
                - html: Formatted HTML timetable (if include_html=True)

        Example:
            >>> timetable = await stop_timetable("Karlsplatz", line="U4")
            >>> print(f"U4 at Karlsplatz: {timetable.total_departures} departures")
            >>> print(f"First: {timetable.first_departure}, Last: {timetable.last_departure}")
        """
        try:
            from database import db
        except ImportError:
            from frontend.database import db

        # Find the stop
        try:
            from data_loader import data_loader
        except ImportError:
            from frontend.data_loader import data_loader

        all_stations = data_loader.load_stations()
        stop_lower = stop.lower().strip()

        # Find matching stop
        matched_stop = None
        for station in all_stations:
            if station.name.lower() == stop_lower:
                matched_stop = station
                break
            if stop_lower in station.name.lower():
                matched_stop = station
                break

        if not matched_stop:
            raise ValueError(f"Stop '{stop}' not found. Try searching with station_search first.")

        # Validate day_type
        if day_type.lower() not in ["weekday", "saturday", "sunday"]:
            day_type = "weekday"

        # Load valid service_ids for the day type from calendar.txt
        valid_services = _load_calendar_services(day_type)

        # Query timetable from database
        # Join: stops -> stop_times -> trips -> routes
        query = """
        SELECT
            s.stop_name,
            s.stop_id,
            st.departure_time,
            r.route_short_name as line,
            t.trip_headsign as direction,
            t.trip_id,
            t.service_id
        FROM stops s
        JOIN stop_times st ON st.stop_id = s.stop_id
        JOIN trips t ON t.trip_id = st.trip_id
        JOIN routes r ON r.route_id = t.route_id
        WHERE LOWER(s.stop_name) LIKE :stop_pattern
        """

        params = {"stop_pattern": f"%{stop_lower}%"}

        if line:
            query += " AND LOWER(r.route_short_name) = LOWER(:line_filter)"
            params["line_filter"] = line

        query += """
        ORDER BY st.departure_time
        LIMIT 10000
        """

        results = db.execute_query(query, params)

        if not results:
            # Return empty timetable
            return StopTimetableResponse(
                stop_name=matched_stop.name,
                stop_id=matched_stop.rbl or "unknown",
                line_filter=line,
                day_type=day_type,
                service_date=datetime.now().strftime("%Y-%m-%d"),
                hours=[],
                total_departures=0,
                first_departure=None,
                last_departure=None,
                lines_serving=[],
                html=None,
            )

        # Get stop info from first result
        stop_name = results[0]["stop_name"]
        stop_id = results[0]["stop_id"]

        # Group by hour, filtering by day type if calendar data available
        hours_data = {h: [] for h in range(24)}
        lines_set = set()
        all_times = []
        filtered_count = 0
        total_count = 0

        for row in results:
            total_count += 1

            # Filter by service_id if we have calendar data
            if valid_services:
                service_id = row.get("service_id", "")
                if service_id not in valid_services:
                    filtered_count += 1
                    continue
            dep_time = row["departure_time"]
            # Handle times like "25:30:00" (next day)
            try:
                parts = dep_time.split(":")
                hour = int(parts[0]) % 24  # Wrap around for next-day times
                time_str = f"{hour:02d}:{parts[1]}"
                all_times.append(dep_time)

                entry = TimetableEntry(
                    time=time_str,
                    line=row["line"] or "?",
                    direction=row["direction"] or "",
                    trip_id=row["trip_id"],
                )
                hours_data[hour].append(entry)
                lines_set.add(row["line"] or "?")
            except (ValueError, IndexError):
                continue

        # Build hour objects
        hours = []
        for h in range(24):
            departures = hours_data[h]
            # Remove duplicates by (time, line)
            seen = set()
            unique_deps = []
            for d in departures:
                key = (d.time, d.line)
                if key not in seen:
                    seen.add(key)
                    unique_deps.append(d)

            hours.append(
                TimetableHour(
                    hour=h,
                    hour_label=f"{h:02d}:00",
                    departures=unique_deps,
                    count=len(unique_deps),
                )
            )

        # Calculate totals
        total = sum(h.count for h in hours)
        first_dep = min(all_times) if all_times else None
        last_dep = max(all_times) if all_times else None

        # Format first/last times
        if first_dep:
            parts = first_dep.split(":")
            first_dep = f"{int(parts[0]) % 24:02d}:{parts[1]}"
        if last_dep:
            parts = last_dep.split(":")
            last_dep = f"{int(parts[0]) % 24:02d}:{parts[1]}"

        response = StopTimetableResponse(
            stop_name=stop_name,
            stop_id=stop_id,
            line_filter=line,
            day_type=day_type,
            service_date=datetime.now().strftime("%Y-%m-%d"),
            hours=hours,
            total_departures=total,
            first_departure=first_dep,
            last_departure=last_dep,
            lines_serving=sorted(lines_set),
            html=None,
        )

        # Generate HTML if requested
        if include_html:
            response.html = _generate_html_timetable(response)

        return response
