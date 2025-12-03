"""
Weather Integration Service
Phase 5: Weather-aware transit predictions and recommendations

Integrates weather data to improve delay predictions and routing suggestions.
Weather affects different transit types differently:
- Trams: Affected by snow, ice, flooding
- Buses: Affected by traffic (rain increases congestion)
- U-Bahn: Mostly unaffected (underground)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from enum import Enum
import requests

logger = logging.getLogger(__name__)


class WeatherCondition(Enum):
    """Weather condition types."""

    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    SNOW = "snow"
    ICE = "ice"
    STORM = "storm"
    FOG = "fog"


class WeatherSeverity(Enum):
    """Weather severity levels."""

    NONE = 0
    MINOR = 1
    MODERATE = 2
    SEVERE = 3


@dataclass
class WeatherData:
    """Current weather conditions."""

    temperature_celsius: float
    condition: WeatherCondition
    severity: WeatherSeverity
    precipitation_mm: float
    wind_speed_kmh: float
    visibility_km: float
    timestamp: datetime

    def affects_transit(self) -> bool:
        """Check if weather affects transit operations."""
        return self.severity.value >= WeatherSeverity.MODERATE.value


@dataclass
class WeatherImpact:
    """Impact of weather on transit services."""

    vehicle_type: str
    delay_factor: float  # Multiplier for normal delays
    recommended: bool
    warning_message: Optional[str]


class WeatherService:
    """Service for weather data and transit impact analysis."""

    # Weather impact on vehicle types
    IMPACT_MATRIX = {
        WeatherCondition.RAIN: {
            "metro": WeatherImpact("metro", 1.0, True, None),
            "tram": WeatherImpact("tram", 1.3, True, "Slight delays possible due to wet tracks"),
            "bus": WeatherImpact(
                "bus", 1.5, False, "Traffic congestion likely - consider metro/tram"
            ),
        },
        WeatherCondition.HEAVY_RAIN: {
            "metro": WeatherImpact("metro", 1.0, True, None),
            "tram": WeatherImpact("tram", 1.5, True, "Moderate delays possible"),
            "bus": WeatherImpact("bus", 2.0, False, "Significant traffic delays expected"),
        },
        WeatherCondition.SNOW: {
            "metro": WeatherImpact("metro", 1.0, True, None),
            "tram": WeatherImpact("tram", 2.0, False, "Snow affects tram service - delays likely"),
            "bus": WeatherImpact("bus", 2.5, False, "Heavy traffic and snow - avoid if possible"),
        },
        WeatherCondition.ICE: {
            "metro": WeatherImpact("metro", 1.0, True, None),
            "tram": WeatherImpact("tram", 3.0, False, "Ice on tracks - service may be disrupted"),
            "bus": WeatherImpact("bus", 3.0, False, "Dangerous conditions - use metro if possible"),
        },
        WeatherCondition.STORM: {
            "metro": WeatherImpact(
                "metro", 1.1, True, "Underground service preferred during storm"
            ),
            "tram": WeatherImpact("tram", 2.5, False, "Storm may disrupt overhead lines"),
            "bus": WeatherImpact("bus", 2.0, False, "Poor visibility and conditions"),
        },
    }

    def __init__(self, api_key: Optional[str] = None, cache_ttl: int = 600):
        """Initialize weather service.

        Args:
            api_key: OpenWeatherMap API key (optional, uses free tier if None)
            cache_ttl: Cache time-to-live in seconds (default: 10 minutes)
        """
        self.api_key = api_key
        self.cache_ttl = cache_ttl
        self._cache: Optional[WeatherData] = None
        self._cache_time: Optional[datetime] = None

        # OpenWeatherMap free tier endpoint
        self.api_base = "https://api.openweathermap.org/data/2.5/weather"

    def get_current_weather(
        self, city: str = "Vienna", use_cache: bool = True
    ) -> Optional[WeatherData]:
        """Get current weather for a city.

        Args:
            city: City name
            use_cache: Use cached data if available

        Returns:
            WeatherData object or None if unavailable
        """
        # Check cache
        if use_cache and self._cache and self._cache_time:
            age = (datetime.now() - self._cache_time).total_seconds()
            if age < self.cache_ttl:
                logger.debug(f"Using cached weather data (age: {age:.0f}s)")
                return self._cache

        # Fetch fresh data
        try:
            weather = self._fetch_weather(city)
            if weather:
                self._cache = weather
                self._cache_time = datetime.now()
            return weather
        except Exception as e:
            logger.error(f"Error fetching weather: {e}", exc_info=True)
            return self._cache  # Return stale cache if available

    def _fetch_weather(self, city: str) -> Optional[WeatherData]:
        """Fetch weather from API."""
        if not self.api_key:
            # Return mock data for testing
            logger.info("No weather API key - returning mock data")
            return self._get_mock_weather()

        try:
            params = {"q": city, "appid": self.api_key, "units": "metric"}

            response = requests.get(self.api_base, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()

            # Parse weather data
            temp = data["main"]["temp"]
            weather_id = data["weather"][0]["id"]
            weather_main = data["weather"][0]["main"].lower()
            precipitation = data.get("rain", {}).get("1h", 0) + data.get("snow", {}).get("1h", 0)
            wind_speed = data["wind"]["speed"] * 3.6  # m/s to km/h
            visibility = data.get("visibility", 10000) / 1000  # meters to km

            # Determine condition and severity
            condition, severity = self._parse_weather_conditions(
                weather_id, weather_main, precipitation, wind_speed, temp
            )

            return WeatherData(
                temperature_celsius=temp,
                condition=condition,
                severity=severity,
                precipitation_mm=precipitation,
                wind_speed_kmh=wind_speed,
                visibility_km=visibility,
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return self._get_mock_weather()

    def _parse_weather_conditions(
        self,
        weather_id: int,
        weather_main: str,
        precipitation: float,
        wind_speed: float,
        temp: float,
    ) -> tuple[WeatherCondition, WeatherSeverity]:
        """Parse weather conditions into standard format."""
        # OpenWeatherMap condition codes
        # 2xx: Thunderstorm, 3xx: Drizzle, 5xx: Rain, 6xx: Snow, 7xx: Atmosphere, 8xx: Clear/Clouds

        condition = WeatherCondition.CLEAR
        severity = WeatherSeverity.NONE

        if weather_id >= 200 and weather_id < 300:  # Thunderstorm
            condition = WeatherCondition.STORM
            severity = WeatherSeverity.SEVERE
        elif weather_id >= 500 and weather_id < 600:  # Rain
            if precipitation > 5:
                condition = WeatherCondition.HEAVY_RAIN
                severity = WeatherSeverity.MODERATE
            else:
                condition = WeatherCondition.RAIN
                severity = WeatherSeverity.MINOR
        elif weather_id >= 600 and weather_id < 700:  # Snow
            condition = WeatherCondition.SNOW
            severity = WeatherSeverity.MODERATE if precipitation > 2 else WeatherSeverity.MINOR
        elif temp < 0 and "rain" in weather_main:  # Freezing rain
            condition = WeatherCondition.ICE
            severity = WeatherSeverity.SEVERE
        elif weather_id == 741:  # Fog
            condition = WeatherCondition.FOG
            severity = WeatherSeverity.MINOR
        elif wind_speed > 50:  # High winds
            condition = WeatherCondition.STORM
            severity = WeatherSeverity.MODERATE

        return condition, severity

    def _get_mock_weather(self) -> WeatherData:
        """Return mock weather data for testing."""
        return WeatherData(
            temperature_celsius=15.0,
            condition=WeatherCondition.CLEAR,
            severity=WeatherSeverity.NONE,
            precipitation_mm=0.0,
            wind_speed_kmh=10.0,
            visibility_km=10.0,
            timestamp=datetime.now(),
        )

    def get_transit_impact(self, weather: Optional[WeatherData] = None) -> dict[str, WeatherImpact]:
        """Get weather impact on different transit types.

        Args:
            weather: Weather data (fetches current if None)

        Returns:
            Dictionary of vehicle_type -> WeatherImpact
        """
        if weather is None:
            weather = self.get_current_weather()

        if not weather or not weather.affects_transit():
            # No significant weather impact
            return {
                "metro": WeatherImpact("metro", 1.0, True, None),
                "tram": WeatherImpact("tram", 1.0, True, None),
                "bus": WeatherImpact("bus", 1.0, True, None),
            }

        # Get impact matrix for current conditions
        return self.IMPACT_MATRIX.get(weather.condition, {})

    def adjust_prediction_for_weather(
        self, base_prediction: float, vehicle_type: str, weather: Optional[WeatherData] = None
    ) -> tuple[float, str]:
        """Adjust delay prediction based on weather.

        Args:
            base_prediction: Base delay prediction in minutes
            vehicle_type: Type of vehicle
            weather: Weather data

        Returns:
            Tuple of (adjusted_prediction, weather_note)
        """
        if weather is None:
            weather = self.get_current_weather()

        if not weather or not weather.affects_transit():
            return base_prediction, ""

        # Get impact for this vehicle type
        impacts = self.get_transit_impact(weather)
        impact = impacts.get(vehicle_type)

        if not impact:
            return base_prediction, ""

        # Apply weather factor
        adjusted = base_prediction * impact.delay_factor

        # Generate weather note
        weather_note = f"Weather: {weather.condition.value.title()}"
        if impact.warning_message:
            weather_note += f" - {impact.warning_message}"

        return adjusted, weather_note

    def get_route_recommendations(self, weather: Optional[WeatherData] = None) -> list[str]:
        """Get route recommendations based on weather.

        Args:
            weather: Weather data

        Returns:
            List of recommendation strings
        """
        if weather is None:
            weather = self.get_current_weather()

        if not weather or not weather.affects_transit():
            return []

        recommendations = []
        impacts = self.get_transit_impact(weather)

        # Recommend underground options in bad weather
        if weather.condition in [
            WeatherCondition.HEAVY_RAIN,
            WeatherCondition.SNOW,
            WeatherCondition.STORM,
        ]:
            recommendations.append("☂️ Prefer U-Bahn (metro) - stays dry and unaffected by weather")

        # Warn about affected services
        for vehicle_type, impact in impacts.items():
            if not impact.recommended and impact.warning_message:
                recommendations.append(f"⚠️ {vehicle_type.title()}: {impact.warning_message}")

        # Cold weather tips
        if weather.temperature_celsius < 0:
            recommendations.append("🥶 Cold weather - stations have heated waiting areas")

        # Hot weather tips
        if weather.temperature_celsius > 30:
            recommendations.append("🌡️ Hot weather - newer U-Bahn trains have AC")

        return recommendations


# Singleton
_weather_service: Optional[WeatherService] = None


def get_weather_service(api_key: Optional[str] = None) -> WeatherService:
    """Get or create weather service instance."""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService(api_key)
    return _weather_service
