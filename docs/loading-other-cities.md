# Loading GTFS Data for Other Cities

This guide explains how to load GTFS data from cities other than Vienna.

## Quick Start

### Option 1: Use Pre-configured City

```powershell
# List available cities
python scripts\download_wienerlinien_data.py --list-cities

# Download and process London GTFS
python scripts\download_wienerlinien_data.py --city london

# Load to database
python scripts\load_gtfs_to_db.py scripts\gtfs_data\london-gtfs.zip
```

### Option 2: Use Custom GTFS URL

```powershell
# Download from any GTFS feed URL
python scripts\download_wienerlinien_data.py --gtfs-url https://example.com/gtfs.zip

# Load to database (skip RBL mapping for non-Vienna cities)
python scripts\load_gtfs_to_db.py scripts\gtfs_data\gtfs.zip
```

### Option 3: Use Environment Variables

```powershell
# Set city via environment variable
$env:GTFS_CITY = "london"
python scripts\gtfs_scheduled_loader.py

# Or use custom URL
$env:GTFS_URL = "https://example.com/gtfs.zip"
python scripts\gtfs_scheduled_loader.py
```

## Pre-configured Cities

The following cities are pre-configured:

- **vienna** - Vienna public transport (Wiener Linien)
- **london** - London public transport (TfL)
- **munich** - Munich public transport (MVV)
- **tokyo** - Tokyo public transport
- **berlin** - Berlin public transport (BVG)
- **paris** - Paris public transport (RATP/IDFM)
- **newyork** - New York public transport (MTA)

## Finding GTFS Feed URLs

### General Sources

1. **Transitland** - https://www.transit.land/feeds
   - Aggregates GTFS feeds from around the world
   - Search by city or agency name

2. **GTFS Data Exchange** - https://www.gtfs-data-exchange.com/
   - Directory of GTFS feeds

3. **MobilityData** - https://database.mobilitydata.org/
   - Comprehensive database of transit feeds

### City-Specific Sources

**Munich/Germany:**
- https://gtfs.de/en/feeds/ - Germany-wide feeds (daily updates)

**London:**
- https://www.transit.land/feeds - Search for "London"
- Transport for London (TfL) open data portal

**Tokyo:**
- https://challenge2025.odpt.org/en/opendata.html
- May require API key registration

**New York:**
- https://www.nyc.gov/assets/mta/downloads/gtfs/google_transit.zip

**Paris:**
- Île-de-France Mobilités open data portal

## Configuration Details

### City Configuration File

City configurations are stored in `scripts/city_config.py`. Each city has:

- `name` - Display name
- `gtfs_url` - GTFS feed URL
- `timezone` - Default timezone (e.g., "Europe/London")
- `language` - Default language code
- `enable_rbl_mapping` - Whether to use Vienna-specific RBL/DIVA mapping (Vienna only)
- `description` - City description

### Adding a New City

Edit `scripts/city_config.py` and add a new entry:

```python
"yourcity": CityConfig(
    name="Your City",
    gtfs_url="https://example.com/gtfs.zip",
    timezone="America/New_York",
    language="en",
    enable_rbl_mapping=False,
    description="Your city public transport"
)
```

## Loading Process

### Step-by-Step

1. **Download GTFS data:**
   ```powershell
   python scripts\download_wienerlinien_data.py --city london
   ```

2. **Load to database:**
   ```powershell
   python scripts\load_gtfs_to_db.py scripts\gtfs_data\london-gtfs.zip
   ```

3. **Verify data:**
   ```powershell
   docker exec wienerlinien-db psql -U wienerlinien -d wienerlinien -c "SELECT COUNT(*) FROM routes; SELECT COUNT(*) FROM stops;"
   ```

### Using Docker

Set environment variables in `docker-compose.yml`:

```yaml
environment:
  - GTFS_CITY=london
  # OR
  - GTFS_URL=https://example.com/gtfs.zip
```

Then run:
```powershell
docker compose up gtfs-loader --profile loader
```

## Important Notes

### RBL Mapping (Vienna-Specific)

- RBL/DIVA mapping is **only for Vienna**
- For other cities, the loader will skip RBL mapping automatically
- Stop codes from the GTFS feed will be used directly

### Timezone Handling

- Each city has a default timezone configured
- The GTFS feed's `agency_timezone` takes precedence
- Falls back to city config timezone if not specified in GTFS

### Database Schema

- The database schema is **generic GTFS** - works with any city
- No city-specific fields required
- All standard GTFS fields are supported

## Troubleshooting

### Common Issues

1. **GTFS URL not accessible:**
   - Verify the URL is publicly accessible
   - Check if authentication/API key is required
   - Some feeds may require registration

2. **Timezone errors:**
   - Ensure the timezone string is valid (e.g., "Europe/London")
   - Check Python's `pytz` or `zoneinfo` support

3. **Large datasets:**
   - Use `--test-mode` for initial testing
   - Increase `chunk_size` for faster loading
   - Some cities have very large datasets (millions of stop_times)

4. **Missing files:**
   - Ensure the GTFS zip contains required files:
     - `routes.txt`
     - `stops.txt`
     - `trips.txt`
     - `stop_times.txt`
     - `agency.txt`

### Performance Tips

- Large cities (Tokyo, New York) may take 30-60 minutes to load
- Use `--test-mode` to verify the feed works before full import
- Monitor disk space - some GTFS feeds are 100+ MB compressed

## Examples

### London

```powershell
# Download London GTFS
python scripts\download_wienerlinien_data.py --city london --force-download

# Load to database
python scripts\load_gtfs_to_db.py scripts\gtfs_data\london-gtfs.zip --test-mode
```

### Munich

```powershell
# Download Munich GTFS (from Germany feed)
python scripts\download_wienerlinien_data.py --city munich

# Load to database
python scripts\load_gtfs_to_db.py scripts\gtfs_data\munich-gtfs.zip
```

### Custom Feed

```powershell
# Download custom feed
python scripts\download_wienerlinien_data.py --gtfs-url https://transit.land/api/v2/feeds/f-9q5-metro~losangeles~rail/versions/latest/download

# Load to database
python scripts\load_gtfs_to_db.py scripts\gtfs_data\gtfs.zip
```

## Next Steps

After loading data for a new city:

1. Verify routes and stops are loaded correctly
2. Test API endpoints (`/api/routes`, `/api/lines`)
3. Update frontend if city-specific features are needed
4. Configure real-time data sources (if available)

## See Also

- [GTFS Specification](https://gtfs.org/schedule/reference/)
- [GTFS-RT Specification](https://gtfs.org/realtime/reference/) (for real-time data)
- [MobilityData GTFS Best Practices](https://gtfs.org/best-practices/)

