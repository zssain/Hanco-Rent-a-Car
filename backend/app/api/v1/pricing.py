"""
Dynamic pricing endpoints for Hanco-AI
ML-powered pricing using ONNX Runtime
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import date, datetime
import logging
import uuid

from app.core.firebase import db, Collections
from app.services.pricing.feature_builder import build_pricing_features
from app.services.pricing.onnx_runtime import predict_price
from google.cloud import firestore

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Schemas ====================

class PricingRequest(BaseModel):
    """Request schema for price calculation"""
    vehicle_id: str = Field(..., description="Vehicle ID")
    city: str = Field(..., description="City name")
    start_date: date = Field(..., description="Rental start date")
    end_date: date = Field(..., description="Rental end date")


class PricingResponse(BaseModel):
    """Response schema for price calculation"""
    vehicle_id: str
    city: str
    rental_length_days: int
    daily_price: float
    total_price: float
    weather: Dict[str, float]
    competitor_summary: Dict[str, float]
    features: Dict[str, float]
    timestamp: datetime


# ==================== Endpoints ====================

@router.post("/calculate", response_model=PricingResponse)
async def calculate_pricing(request: PricingRequest):
    """
    Calculate dynamic price for a vehicle rental
    
    Uses ML model (ONNX) with:
    - Temporal features (day, month, rental length)
    - Weather data (temperature, rain, wind)
    - Competitor pricing
    - Demand index
    - Vehicle base rate
    
    Returns total price and breakdown.
    """
    try:
        # Validate dates
        if request.end_date <= request.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
        
        if request.start_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be in the past"
            )
        
        # Get vehicle from Firestore
        vehicle_ref = db.collection(Collections.VEHICLES).document(request.vehicle_id)
        vehicle_doc = vehicle_ref.get()
        
        if not vehicle_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle with ID {request.vehicle_id} not found"
            )
        
        vehicle_data = vehicle_doc.to_dict()
        
        # Build features
        features = await build_pricing_features(
            vehicle_doc=vehicle_data,
            start_date=request.start_date,
            end_date=request.end_date,
            city=request.city,
            firestore_client=db
        )
        
        # Predict daily price using ONNX model
        daily_price = predict_price(features)
        
        # Calculate total price
        rental_length_days = (request.end_date - request.start_date).days
        total_price = daily_price * rental_length_days
        
        # Prepare response data
        weather_summary = {
            'avg_temp': features['avg_temp'],
            'rain': features['rain'],
            'wind': features['wind']
        }
        
        competitor_summary = {
            'avg_competitor_price': features['avg_competitor_price']
        }
        
        # Save pricing log to Firestore
        log_id = str(uuid.uuid4())
        pricing_log = {
            'id': log_id,
            'vehicle_id': request.vehicle_id,
            'city': request.city,
            'start_date': request.start_date.isoformat(),
            'end_date': request.end_date.isoformat(),
            'rental_length_days': rental_length_days,
            'features': features,
            'daily_price': daily_price,
            'total_price': total_price,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        
        db.collection(Collections.PRICING_LOGS).document(log_id).set(pricing_log)
        
        logger.info(
            f"Pricing calculated: {request.vehicle_id} in {request.city} "
            f"for {rental_length_days} days = ${total_price:.2f}"
        )
        
        return PricingResponse(
            vehicle_id=request.vehicle_id,
            city=request.city,
            rental_length_days=rental_length_days,
            daily_price=round(daily_price, 2),
            total_price=round(total_price, 2),
            weather=weather_summary,
            competitor_summary=competitor_summary,
            features=features,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating pricing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate pricing: {str(e)}"
        )
