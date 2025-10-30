import os
from dotenv import load_dotenv


load_dotenv()


ROBOFLOW_API_URL = os.getenv("ROBOFLOW_API_URL", "https://serverless.roboflow.com")

ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")

ROBOFLOW_MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID", "cloud-types2-vljyy/1")



OPENWEATHER_API_KEY = os.getenv("weatherLOC") or os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"


if not OPENWEATHER_API_KEY:

	pass

# App Configuration
APP_TITLE = "Cloud Detection & Weather Monitoring"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "FastAPI backend for cloud detection using Roboflow and weather data from OpenWeatherMap"
 

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")