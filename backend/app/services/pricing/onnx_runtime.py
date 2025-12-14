"""
ONNX Runtime Inference Service
Loads the ONNX model and performs price predictions
"""
import numpy as np
import onnxruntime as ort
from typing import Dict
import os
import logging

logger = logging.getLogger(__name__)

# Feature order (must match training)
FEATURE_ORDER = [
    'rental_length_days',
    'day_of_week',
    'month',
    'base_daily_rate',
    'avg_temp',
    'rain',
    'wind',
    'avg_competitor_price',
    'demand_index',
    'bias'
]


class ONNXPricingModel:
    """ONNX model wrapper for price prediction"""
    
    def __init__(self):
        self.session = None
        self.model_path = None
        self._load_model()
    
    def _load_model(self):
        """Load the ONNX model once at initialization"""
        try:
            # Get model path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.model_path = os.path.join(
                current_dir, 
                '..', 
                '..', 
                'ml', 
                'models', 
                'model.onnx'
            )
            
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(
                    f"ONNX model not found at {self.model_path}. "
                    f"Run: python app/ml/training/create_dummy_model.py"
                )
            
            # Create inference session
            self.session = ort.InferenceSession(self.model_path)
            logger.info(f"✅ ONNX model loaded from: {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {str(e)}")
            raise
    
    def predict_price(self, features: Dict[str, float]) -> float:
        """
        Predict price using ONNX model
        
        Args:
            features: Dictionary of feature name -> value
            
        Returns:
            Predicted daily price
            
        Raises:
            ValueError: If required features are missing
        """
        try:
            # Validate features
            missing_features = [f for f in FEATURE_ORDER if f not in features]
            if missing_features:
                raise ValueError(f"Missing features: {missing_features}")
            
            # Convert dict to ordered numpy array
            feature_vector = np.array([
                [features[f] for f in FEATURE_ORDER]
            ], dtype=np.float32)
            
            # Run inference - model expects 'features' as input name
            result = self.session.run(None, {'features': feature_vector})
            predicted_price = float(result[0][0][0])
            
            logger.info(f"Predicted price: ${predicted_price:.2f}")
            
            return predicted_price
            
        except Exception as e:
            logger.error(f"Error predicting price: {str(e)}")
            raise


# Global singleton instance
_model_instance = None


def get_pricing_model() -> ONNXPricingModel:
    """Get or create the global pricing model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = ONNXPricingModel()
    return _model_instance


def predict_price(features: Dict[str, float]) -> float:
    """
    Convenience function for price prediction
    
    Args:
        features: Dictionary with keys:
            - rental_length_days
            - day_of_week
            - month
            - base_daily_rate
            - avg_temp
            - rain
            - wind
            - avg_competitor_price
            - demand_index
            - bias
    
    Returns:
        Predicted daily price as float
    """
    model = get_pricing_model()
    return model.predict_price(features)
