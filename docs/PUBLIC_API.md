# MyWienerLinien Public API Documentation

**Version**: 1.0.0  
**Base URL**: `http://localhost:3079/api/v1`  
**Phase**: 4 - Multi-City & Developer Access  
**Date**: 2025-12-03

---

## Overview

The MyWienerLinien Public API provides programmatic access to Vienna (and Austrian) public transport data, including real-time departures, journey planning, ML delay predictions, and analytics.

### Features

- ✅ Real-time departure information
- ✅ Station search and information
- ✅ Journey planning with A* routing
- ✅ ML-based delay predictions
- ✅ Multi-city support (Austrian cities)
- ✅ Rate limiting (60 req/min per key)
- ✅ RESTful design
- ✅ JSON responses

---

## Authentication

All API endpoints require an API key sent via header:

```http
X-API-Key: your-api-key-here
```

### Getting an API Key

**Development/Testing:**
```bash
# Generate a test key (admin access required)
curl -X POST http://localhost:3079/admin/api-keys \
  -H "Content-Type: application/json" \
  -d '{"name": "My App", "created_by": "developer@example.com"}'
```

**Production:**
Contact: admin@mywienerlinien.com (or self-service portal - TBD)

---

## Rate Limiting

- **Limit**: 60 requests per minute per API key
- **Headers**: Response includes `X-RateLimit-Remaining`
- **Exceeded**: Returns 429 status with `Retry-After` header

**Example Response Headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1638360000
```

---

## Endpoints

### 1. API Information

**GET /api/v1/**

Get API information and available endpoints.

**Request:**
```bash
curl http://localhost:3079/api/v1/
```

**Response:**
```json
{
  "name": "Wiener Linien Live Map Public API",
  "version": "1.0.0",
  "documentation": "/api/v1/docs",
  "authentication": "X-API-Key header required",
  "rate_limit": "60 requests per minute",
  "endpoints": {
    "departures": "/api/v1/departures",
    "stations": "/api/v1/stations",
    "journey": "/api/v1/journey",
    "predictions": "/api/v1/predictions",
    "cities": "/api/v1/cities"
  }
}
```

---

### 2. Real-time Departures

**GET /api/v1/departures**

Get next departures from a station.

**Parameters:**
- `station` (required): Station name
- `limit` (optional): Maximum departures (1-10, default: 5)

**Request:**
```bash
curl "http://localhost:3079/api/v1/departures?station=Stephansplatz&limit=5" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "station": "Stephansplatz",
  "departures": [
    {
      "line": "U1",
      "destination": "Leopoldau",
      "countdown_minutes": 2,
      "departure_time": "2025-12-03T14:32:00Z",
      "vehicle_type": "metro",
      "platform": "1"
    }
  ],
  "count": 5,
  "rate_limit_remaining": 55,
  "timestamp": "2025-12-03T14:30:00Z"
}
```

---

### 3. Station Search

**GET /api/v1/stations**

Search for stations by name.

**Parameters:**
- `query` (optional): Search query (partial match, returns all if None)
- `limit` (optional): Maximum results (1-50, default: 10)

**Request:**
```bash
curl "http://localhost:3079/api/v1/stations?query=Stephans&limit=10" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "stations": [
    {
      "id": "stop_123",
      "name": "Stephansplatz",
      "lat": 48.2085,
      "lng": 16.3720
    }
  ],
  "count": 1,
  "query": "Stephans",
  "rate_limit_remaining": 54,
  "timestamp": "2025-12-03T14:30:00Z"
}
```

---

### 4. Journey Planning

**GET /api/v1/journey**

Plan journey between two stations with A* routing.

**Parameters:**
- `from_station` (required): Origin station name
- `to_station` (required): Destination station name
- `alternatives` (optional): Number of route options (1-5, default: 3)

**Request:**
```bash
curl "http://localhost:3079/api/v1/journey?from_station=Stephansplatz&to_station=Praterstern&alternatives=3" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "routes": [
    {
      "from": "Stephansplatz",
      "to": "Praterstern",
      "duration_minutes": 5,
      "transfers": 0,
      "cost": "€2.40",
      "segments": [
        {
          "line": "U1",
          "from": "Stephansplatz",
          "to": "Praterstern",
          "duration": 5,
          "vehicle_type": "metro"
        }
      ]
    }
  ],
  "count": 1,
  "rate_limit_remaining": 53,
  "timestamp": "2025-12-03T14:30:00Z"
}
```

---

### 5. ML Delay Predictions

**GET /api/v1/predictions/{line}**

Get machine learning delay prediction for a line.

**Parameters:**
- `line` (path): Line code (e.g., "U1", "U3")

**Request:**
```bash
curl "http://localhost:3079/api/v1/predictions/U1" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "line": "U1",
  "predicted_delay_minutes": 3.2,
  "confidence": 0.82,
  "timestamp": "2025-12-03T14:30:00Z",
  "rate_limit_remaining": 52
}
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "API key required. Get your key at /api/v1/docs"
}
```

### 429 Rate Limit Exceeded
```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds."
}
```
**Headers**: `Retry-After: 45`

### 404 Not Found
```json
{
  "detail": "Station 'InvalidStation' not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Journey planning failed: [error details]"
}
```

---

## Rate Limits

| Tier | Requests/Minute | Cost |
|------|-----------------|------|
| **Free** | 60 | Free |
| **Developer** | 600 | $10/month |
| **Enterprise** | Unlimited | Custom |

Contact for higher limits.

---

## Best Practices

### 1. Cache Responses
Cache station lists and static data locally. Only query real-time data (departures, predictions) frequently.

### 2. Handle Rate Limits
```python
import time
response = requests.get(url, headers=headers)
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    time.sleep(retry_after)
    response = requests.get(url, headers=headers)
```

### 3. Use Batch Requests
When possible, fetch multiple stations/lines in one request.

### 4. Monitor Usage
Track your API usage via dashboard (coming soon).

---

## Code Examples

### Python

```python
import requests

API_BASE = "http://localhost:3079/api/v1"
API_KEY = "your-api-key-here"

headers = {"X-API-Key": API_KEY}

# Get departures
response = requests.get(
    f"{API_BASE}/departures",
    params={"station": "Stephansplatz", "limit": 5},
    headers=headers
)
departures = response.json()

# Plan journey
response = requests.get(
    f"{API_BASE}/journey",
    params={
        "from_station": "Stephansplatz",
        "to_station": "Praterstern",
        "alternatives": 3
    },
    headers=headers
)
journey = response.json()

# Get prediction
response = requests.get(
    f"{API_BASE}/predictions/U1",
    headers=headers
)
prediction = response.json()
```

### JavaScript

```javascript
const API_BASE = 'http://localhost:3079/api/v1';
const API_KEY = 'your-api-key-here';

const headers = {
    'X-API-Key': API_KEY
};

// Get departures
const response = await fetch(
    `${API_BASE}/departures?station=Stephansplatz&limit=5`,
    { headers }
);
const data = await response.json();

// Plan journey
const journey = await fetch(
    `${API_BASE}/journey?from_station=Stephansplatz&to_station=Praterstern`,
    { headers }
).then(r => r.json());

// Get prediction
const prediction = await fetch(
    `${API_BASE}/predictions/U1`,
    { headers }
).then(r => r.json());
```

### curl

```bash
#!/bin/bash
API_KEY="your-api-key-here"

# Get departures
curl "http://localhost:3079/api/v1/departures?station=Stephansplatz&limit=5" \
  -H "X-API-Key: $API_KEY"

# Plan journey
curl "http://localhost:3079/api/v1/journey?from_station=Stephansplatz&to_station=Praterstern" \
  -H "X-API-Key: $API_KEY"

# Get prediction
curl "http://localhost:3079/api/v1/predictions/U1" \
  -H "X-API-Key: $API_KEY"
```

---

## Multi-City Support

### Available Cities

- **Vienna** (vienna) - Wiener Linien (U-Bahn, trams, buses) ✅ Data loaded
- **Graz** (graz) - Holding Graz (trams, buses) ⏳ Data pending
- **Linz** (linz) - Linz AG (trams, buses) ⏳ Data pending
- **Salzburg** (salzburg) - Salzburg AG (buses) ⏳ Data pending
- **Innsbruck** (innsbruck) - IVB (trams, buses) ⏳ Data pending
- **ÖBB** (oebb) - Austrian Federal Railways ⏳ Data pending

### Get Cities List

```bash
curl "http://localhost:3079/api/cities" \
  -H "X-API-Key: $API_KEY"
```

### Switch City Context

```bash
curl -X POST "http://localhost:3079/api/cities/graz/switch" \
  -H "X-API-Key: $API_KEY"
```

**Note**: Subsequent API calls will use the switched city context.

---

## Use Cases

### 1. Transit App Integration
Build a mobile/web app using real-time Vienna transit data.

### 2. Smart Home Integration
"Alexa, when's the next U3 from Stephansplatz?"

### 3. Travel Planning Tools
Integrate Austrian city transit into travel apps.

### 4. Research & Analytics
Analyze transit patterns, delays, reliability.

### 5. IoT Displays
Display upcoming departures on smart displays.

---

## Support

- **Documentation**: This file + `/api/v1/docs`
- **Issues**: GitHub Issues
- **Email**: admin@mywienerlinien.com (placeholder)
- **Status**: https://status.mywienerlinien.com (future)

---

## Changelog

### v1.0.0 (2025-12-03) - Phase 4
- Initial public API release
- Real-time departures endpoint
- Station search endpoint
- Journey planning endpoint
- ML predictions endpoint
- Multi-city support (5 Austrian cities)
- Rate limiting (60 req/min)
- API key authentication
- Usage tracking

---

## Terms of Service

- **Data Source**: Wiener Linien Open Data (CC BY 4.0)
- **Fair Use**: Respect rate limits
- **Attribution**: Required for public use
- **Commercial Use**: Contact for licensing
- **No Warranty**: Data provided as-is
- **Privacy**: No personal data collected

---

## Roadmap

### v1.1 (Q1 2025)
- [ ] WebSocket real-time updates
- [ ] Batch request endpoint
- [ ] Historical data export API
- [ ] GraphQL interface
- [ ] Swagger/OpenAPI 3.0 spec

### v1.2 (Q2 2025)
- [ ] OAuth2 authentication
- [ ] User dashboard
- [ ] Usage analytics
- [ ] Webhook notifications
- [ ] Higher tier limits

---

**MyWienerLinien Public API** - Powered by GTFS, A*, and Machine Learning 🚀

