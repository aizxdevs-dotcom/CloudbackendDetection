from inference_sdk import InferenceHTTPClient
from config import ROBOFLOW_API_URL, ROBOFLOW_API_KEY, ROBOFLOW_MODEL_ID
import logging

logger = logging.getLogger(__name__)

class RoboflowService:
    """Service for cloud detection using Roboflow API"""

    def __init__(self):
        """Prepare service. Client initialization is deferred until needed so
        the app can start even if the API key is not yet configured.
        """
        self.client = None
        self.model_id = ROBOFLOW_MODEL_ID
        # Keep configuration values but do not raise here; raise only when used.
        if not ROBOFLOW_API_KEY:
            logger.warning("Roboflow API key not configured. Set ROBOFLOW_API_KEY in .env to enable inference.")
    
    def detect_clouds(self, image_path: str) -> dict:
        """
        Detect cloud types in an image
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Detection results from Roboflow API
        """
        try:
            # Ensure client is initialized (lazy init)
            self._ensure_client()
            result = self.client.infer(image_path, model_id=self.model_id)
            
            # Process and format the results
            formatted_result = self._format_predictions(result)
            
            logger.info(f"Successfully processed image: {image_path}")
            return formatted_result
        
        except Exception as e:
            logger.error(f"Error during cloud detection: {e}")
            raise Exception(f"Cloud detection failed: {str(e)}")

    def _ensure_client(self):
        """Initialize the Roboflow client if it hasn't been created yet.

        Raises a descriptive exception when the API key is missing.
        """
        if self.client is not None:
            return

        if not ROBOFLOW_API_KEY:
            raise Exception("Roboflow API key is not set. Please set ROBOFLOW_API_KEY in your .env file.")

        try:
            self.client = InferenceHTTPClient(
                api_url=ROBOFLOW_API_URL,
                api_key=ROBOFLOW_API_KEY
            )
            logger.info("Roboflow client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Roboflow client: {e}")
            raise
    
    def _format_predictions(self, raw_result: dict) -> dict:
        """
        Format the raw Roboflow API response
        
        Args:
            raw_result (dict): Raw response from Roboflow API
            
        Returns:
            dict: Formatted prediction results
        """
        try:
            formatted = {
                "model_id": raw_result.get("model_id", self.model_id),
                "image_dimensions": {
                    "width": raw_result.get("image", {}).get("width"),
                    "height": raw_result.get("image", {}).get("height")
                },
                "predictions": [],
                "summary": {
                    "total_detections": 0,
                    "confidence_threshold": 0.5
                }
            }
            
            predictions = raw_result.get("predictions", [])
            formatted["summary"]["total_detections"] = len(predictions)
            
            for prediction in predictions:
                formatted_prediction = {
                    "class": prediction.get("class"),
                    "confidence": round(prediction.get("confidence", 0), 3),
                    "bounding_box": {
                        "x": prediction.get("x"),
                        "y": prediction.get("y"),
                        "width": prediction.get("width"),
                        "height": prediction.get("height")
                    }
                }
                formatted["predictions"].append(formatted_prediction)
            
            # Sort predictions by confidence
            formatted["predictions"].sort(key=lambda x: x["confidence"], reverse=True)
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting predictions: {e}")
            return raw_result  # Return raw result if formatting fails