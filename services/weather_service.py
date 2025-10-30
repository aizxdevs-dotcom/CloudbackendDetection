import aiohttp
from typing import Dict, Any, Optional
from config import OPENWEATHER_API_KEY, OPENWEATHER_BASE_URL
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    """Service for fetching weather data from OpenWeatherMap API"""
    
    def __init__(self):
        """Initialize the weather service"""
        self.api_key = OPENWEATHER_API_KEY
        self.base_url = OPENWEATHER_BASE_URL
        
        if self.api_key == "your_openweather_api_key_here":
            logger.warning("OpenWeatherMap API key not configured. Please set OPENWEATHER_API_KEY environment variable.")
    
    async def get_current_weather(self, location: str) -> Dict[str, Any]:
        """
        Get current weather data for a location
        
        Args:
            location (str): City name or "city,country_code"
            
        Returns:
            Dict[str, Any]: Current weather data
        """
        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric"  # Use Celsius
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_current_weather(data)
                    elif response.status == 401:
                        raise Exception("Invalid API key for OpenWeatherMap")
                    elif response.status == 404:
                        raise Exception(f"Location '{location}' not found")
                    else:
                        raise Exception(f"Weather API error: {response.status}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching weather: {e}")
            raise Exception("Unable to connect to weather service")
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            raise
    
    async def get_forecast(self, location: str, days: int = 5) -> Dict[str, Any]:
        """
        Get weather forecast for a location
        
        Args:
            location (str): City name or "city,country_code"
            days (int): Number of days for forecast (1-5)
            
        Returns:
            Dict[str, Any]: Weather forecast data
        """
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric",
                "cnt": min(days * 8, 40)  # 8 forecasts per day (3-hour intervals), max 40
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_forecast(data, days)
                    elif response.status == 401:
                        raise Exception("Invalid API key for OpenWeatherMap")
                    elif response.status == 404:
                        raise Exception(f"Location '{location}' not found")
                    else:
                        raise Exception(f"Weather API error: {response.status}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching forecast: {e}")
            raise Exception("Unable to connect to weather service")
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            raise
    
    def _format_current_weather(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format current weather data from OpenWeatherMap API
        
        Args:
            raw_data (Dict[str, Any]): Raw API response
            
        Returns:
            Dict[str, Any]: Formatted weather data
        """
        try:
            return {
                "location": {
                    "name": raw_data.get("name"),
                    "country": raw_data.get("sys", {}).get("country"),
                    "coordinates": {
                        "lat": raw_data.get("coord", {}).get("lat"),
                        "lon": raw_data.get("coord", {}).get("lon")
                    }
                },
                "current": {
                    "temperature": round(raw_data.get("main", {}).get("temp", 0), 1),
                    "feels_like": round(raw_data.get("main", {}).get("feels_like", 0), 1),
                    "humidity": raw_data.get("main", {}).get("humidity"),
                    "pressure": raw_data.get("main", {}).get("pressure"),
                    "description": raw_data.get("weather", [{}])[0].get("description", "").title(),
                    "main": raw_data.get("weather", [{}])[0].get("main"),
                    "icon": raw_data.get("weather", [{}])[0].get("icon"),
                    "visibility": raw_data.get("visibility", 0) / 1000,  # Convert to km
                    "uv_index": None  # Not available in current weather endpoint
                },
                "wind": {
                    "speed": raw_data.get("wind", {}).get("speed"),
                    "direction": raw_data.get("wind", {}).get("deg"),
                    "gust": raw_data.get("wind", {}).get("gust")
                },
                "clouds": {
                    "coverage": raw_data.get("clouds", {}).get("all")
                },
                "sun": {
                    "sunrise": raw_data.get("sys", {}).get("sunrise"),
                    "sunset": raw_data.get("sys", {}).get("sunset")
                },
                "timestamp": raw_data.get("dt")
            }
        except Exception as e:
            logger.error(f"Error formatting current weather data: {e}")
            return raw_data
    
    def _format_forecast(self, raw_data: Dict[str, Any], days: int) -> Dict[str, Any]:
        """
        Format forecast data from OpenWeatherMap API
        
        Args:
            raw_data (Dict[str, Any]): Raw API response
            days (int): Number of days requested
            
        Returns:
            Dict[str, Any]: Formatted forecast data
        """
        try:
            city_info = raw_data.get("city", {})
            forecasts = raw_data.get("list", [])
            
            formatted_forecasts = []
            for forecast in forecasts[:days * 8]:  # Limit to requested days
                formatted_forecast = {
                    "datetime": forecast.get("dt"),
                    "temperature": {
                        "current": round(forecast.get("main", {}).get("temp", 0), 1),
                        "min": round(forecast.get("main", {}).get("temp_min", 0), 1),
                        "max": round(forecast.get("main", {}).get("temp_max", 0), 1),
                        "feels_like": round(forecast.get("main", {}).get("feels_like", 0), 1)
                    },
                    "humidity": forecast.get("main", {}).get("humidity"),
                    "pressure": forecast.get("main", {}).get("pressure"),
                    "weather": {
                        "main": forecast.get("weather", [{}])[0].get("main"),
                        "description": forecast.get("weather", [{}])[0].get("description", "").title(),
                        "icon": forecast.get("weather", [{}])[0].get("icon")
                    },
                    "wind": {
                        "speed": forecast.get("wind", {}).get("speed"),
                        "direction": forecast.get("wind", {}).get("deg"),
                        "gust": forecast.get("wind", {}).get("gust")
                    },
                    "clouds": {
                        "coverage": forecast.get("clouds", {}).get("all")
                    },
                    "precipitation": {
                        "probability": forecast.get("pop", 0) * 100  # Convert to percentage
                    }
                }
                formatted_forecasts.append(formatted_forecast)
            
            return {
                "location": {
                    "name": city_info.get("name"),
                    "country": city_info.get("country"),
                    "coordinates": {
                        "lat": city_info.get("coord", {}).get("lat"),
                        "lon": city_info.get("coord", {}).get("lon")
                    }
                },
                "forecast": formatted_forecasts,
                "forecast_days": days
            }
            
        except Exception as e:
            logger.error(f"Error formatting forecast data: {e}")
            return raw_data

    # History-related functionality removed per request; this service now
    # focuses on current weather and forecast via OpenWeatherMap only.