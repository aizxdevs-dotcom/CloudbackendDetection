from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import io
from PIL import Image
import tempfile
import os
import asyncio
from typing import Optional, Tuple

from config import (
    APP_TITLE,
    APP_VERSION,
    APP_DESCRIPTION,
    FRONTEND_URL,
    ROBOFLOW_API_KEY,
    ROBOFLOW_MODEL_ID,
    OPENWEATHER_API_KEY,
)
from services.roboflow_service import RoboflowService
from services.weather_service import WeatherService

# Initialize FastAPI app
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION
)


cors_origins = [
    FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://cloud-d-weather.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in cors_origins if o],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
    max_age=600,
)


roboflow_service = RoboflowService()
weather_service = WeatherService()


INFERENCE_QUEUE_MAXSIZE = int(os.getenv("INFERENCE_QUEUE_MAXSIZE", "4"))
INFERENCE_REQUEST_TIMEOUT = float(os.getenv("INFERENCE_REQUEST_TIMEOUT", "15"))  # seconds
inference_queue: "asyncio.Queue[Tuple[asyncio.Future, str, str]]" = asyncio.Queue(maxsize=INFERENCE_QUEUE_MAXSIZE)


async def _inference_worker() -> None:
    """Background worker that processes inference requests from the queue one-by-one.

    Each queued item is a tuple (future, temp_file_path, original_filename). The
    worker runs the blocking Roboflow client in a thread to avoid blocking the
    event loop.
    """
    while True:
        future, temp_path, orig_filename = await inference_queue.get()
        try:
            # Run the blocking detection in a threadpool
            result = await asyncio.to_thread(roboflow_service.detect_clouds, temp_path)
            if not future.done():
                future.set_result({
                    "success": True,
                    "filename": orig_filename,
                    "predictions": result,
                })
        except Exception as e:
            if not future.done():
                future.set_exception(e)
        finally:
            # Attempt to remove temp file; ignore errors
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass
            inference_queue.task_done()


@app.on_event("startup")
async def startup_event_queue():
    # Start background worker
    asyncio.create_task(_inference_worker())

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Cloud Detection & Weather API",
        "version": APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Return health information including presence of required API keys.

    This is useful for the frontend to detect missing configuration before
    attempting user-facing operations (like live inference).
    """
    missing = []
    if not ROBOFLOW_API_KEY:
        missing.append("ROBOFLOW_API_KEY")
    if not ROBOFLOW_MODEL_ID:
        missing.append("ROBOFLOW_MODEL_ID")
    if not OPENWEATHER_API_KEY:
        missing.append("OPENWEATHER_API_KEY")

    return JSONResponse(content={
        "success": True,
        "service": "cloud-detection",
        "missing_keys": missing,
        "healthy": len(missing) == 0,
    })

@app.post("/detect-clouds")
async def detect_clouds(file: UploadFile = File(...)):
    """
    Detect cloud types in an uploaded image using Roboflow model
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data and write to a temporary file. The file is handed off to
        # the background inference worker which is responsible for cleanup.
        image_data = await file.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name

        # Enqueue the request. If the queue is full, return 429 so the client can
        # back off (the frontend LiveStream has an FPS slider to help control rate).
        try:
            future: asyncio.Future = asyncio.get_running_loop().create_future()
            # Attempt to put without waiting — if full, raise immediately
            inference_queue.put_nowait((future, temp_file_path, file.filename))
        except asyncio.QueueFull:
            # Clean up temp file since worker won't handle it
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
            raise HTTPException(status_code=429, detail="Server is busy. Please slow down live uploads or reduce FPS.")

        # Wait for the inference result with a timeout so requests don't hang
        try:
            result = await asyncio.wait_for(future, timeout=INFERENCE_REQUEST_TIMEOUT)
            return JSONResponse(content=result)
        except asyncio.TimeoutError:
            # If the request times out, the worker may still finish later, but
            # we inform the client to retry or lower the rate.
            raise HTTPException(status_code=503, detail="Inference timeout. Try reducing FPS or retrying.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/weather")
async def get_weather(
    city: str = Query(..., description="City name"),
    country: Optional[str] = Query(None, description="Country code (optional)")
):
    """
    Get current weather data for a specified city
    """
    try:
        location = f"{city},{country}" if country else city
        weather_data = await weather_service.get_current_weather(location)
        return JSONResponse(content={
            "success": True,
            "location": location,
            "weather": weather_data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")

@app.get("/weather/forecast")
async def get_weather_forecast(
    city: str = Query(..., description="City name"),
    country: Optional[str] = Query(None, description="Country code (optional)"),
    days: int = Query(5, description="Number of days for forecast (1-5)")
):
    """
    Get weather forecast for a specified city
    """
    try:
        if days < 1 or days > 5:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 5")
        
        location = f"{city},{country}" if country else city
        forecast_data = await weather_service.get_forecast(location, days)
        return JSONResponse(content={
            "success": True,
            "location": location,
            "forecast": forecast_data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching forecast: {str(e)}")


# History endpoints removed as requested

@app.post("/analyze")
async def analyze_clouds_and_weather(
    file: UploadFile = File(...),
    city: str = Query(..., description="City name"),
    country: Optional[str] = Query(None, description="Country code (optional)")
):
    """
    Combined endpoint: detect clouds in image and get weather data for location
    """
    try:
        # Process cloud detection
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        image_data = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name
        
        try:
            # Run cloud detection
            cloud_result = roboflow_service.detect_clouds(temp_file_path)
            
            # Get weather data
            location = f"{city},{country}" if country else city
            weather_data = await weather_service.get_current_weather(location)
            
            return JSONResponse(content={
                "success": True,
                "filename": file.filename,
                "location": location,
                "cloud_detection": cloud_result,
                "weather": weather_data
            })
        finally:
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
