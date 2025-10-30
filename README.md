# Cloud Detection & Weather API

A FastAPI backend that combines cloud detection using Roboflow's machine learning model with weather data from OpenWeatherMap.

## Features

- **Cloud Detection**: Upload images to detect cloud types using a trained Roboflow model
- **Weather Data**: Get current weather and forecasts for any location
- **Combined Analysis**: Analyze both cloud patterns and weather conditions together
- **RESTful API**: Easy-to-use endpoints with comprehensive documentation

## Setup

### 1. Create and activate virtual environment
```bash
cd CloudDW
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Copy `.env` file and add your OpenWeatherMap API key:
```bash
cp .env .env.local
# Edit .env.local and replace 'your_openweather_api_key_here' with your actual API key
```

Get your free OpenWeatherMap API key from: https://openweathermap.org/api

### 4. Run the application
```bash
python main.py
```

The API will be available at: http://localhost:8000

## API Endpoints

### Health Check
- `GET /` - Check if the API is running

### Cloud Detection
- `POST /detect-clouds` - Upload an image to detect cloud types
  - Body: Form data with image file
  - Returns: Cloud detection results with bounding boxes and confidence scores

### Weather Data
- `GET /weather?city={city}&country={country}` - Get current weather
- `GET /weather/forecast?city={city}&country={country}&days={1-5}` - Get weather forecast

### Combined Analysis
- `POST /analyze` - Analyze both clouds and weather
  - Body: Form data with image file
  - Query params: city, country (optional)
  - Returns: Both cloud detection and weather data

## API Documentation

When the server is running, visit:
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Example Usage

### Upload image for cloud detection
```bash
curl -X POST "http://localhost:8000/detect-clouds" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/image.jpg"
```

### Get weather data
```bash
curl "http://localhost:8000/weather?city=London&country=UK"
```

### Combined analysis
```bash
curl -X POST "http://localhost:8000/analyze?city=London&country=UK" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/image.jpg"
```

## Project Structure

```
CloudDW/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables template
├── services/
│   ├── __init__.py
│   ├── roboflow_service.py    # Cloud detection service
│   └── weather_service.py     # Weather data service
└── venv/                  # Virtual environment
```

## Technologies Used

- **FastAPI**: Modern, fast web framework for building APIs
- **Roboflow**: Machine learning platform for computer vision
- **OpenWeatherMap**: Weather data API
- **Pillow**: Python imaging library
- **aiohttp**: Async HTTP client for weather API calls

## Notes

- The Roboflow model is pre-configured for cloud type detection
- Images are temporarily stored during processing and automatically cleaned up
- Weather data includes current conditions and 5-day forecasts
- All endpoints include proper error handling and validation

## Deploying to Render

If you deploy this project to Render, use the following build script to ensure packaging tools are up-to-date and dependencies install correctly (this upgrades pip/setuptools/wheel so Pillow and other binary wheels are preferred over source builds):

1. Add the following as the Build Command in the Render service settings, or use the `render-build.sh` script included in this repo:

```bash
./render-build.sh
```

2. The `render-build.sh` script runs:

```bash
#!/usr/bin/env bash
set -euo pipefail
# Upgrade pip/setuptools/wheel/build to avoid PEP517 build issues
python -m pip install --upgrade pip setuptools wheel build
# Install requirements
python -m pip install -r requirements.txt
```

3. Ensure Render uses Python 3.12 for this project (the repo contains `runtime.txt` set to `python-3.12.3`). Render may default to a different Python; set the runtime in the Render dashboard to match `runtime.txt` so prebuilt wheels for Pillow are used.

If you still hit build failures on Render, temporarily set a verbose install command to capture the failing package:

```bash
python -m pip install --upgrade pip setuptools wheel build
python -m pip -v install -r requirements.txt
```

This will show whether `pip` downloads wheels or attempts source builds (which usually require additional OS-level libraries).

## Docker (optional, reproducible deploy)

If you prefer to deploy with Docker (recommended when you need precise OS-level dependencies), a `Dockerfile` is included which builds using Python 3.12 and installs the common native libraries Pillow might need. To build and run locally:

```bash
# Build the image
docker build -t cloudbackenddetection:latest .

# Run the container (maps port 8000)
docker run --rm -p 8000:8000 cloudbackenddetection:latest
```

On Render you can switch the service to "Docker" deploy and it will build the image using the repository `Dockerfile`. This solves build-time issues by providing the necessary OS packages inside the image.