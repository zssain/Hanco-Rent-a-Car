"""
Pricing request/response schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date


class PricingRequest(BaseModel):
    """Dynamic pricing calculation request"""
    vehicle_id: str
    city: str
    start_date: date
    end_date: date
    
    class Config:
        json_schema_extra = {
            "example": {
                "vehicle_id": "vehicle_123",
                "city": "Riyadh",
                "start_date": "2025-01-15",
                "end_date": "2025-01-20"
            }
        }


class PricingFactors(BaseModel):
    """Pricing factors breakdown"""
    base_rate: float
    weather_factor: float = 1.0
    competitor_factor: float = 1.0
    demand_factor: float = 1.0
    seasonal_factor: float = 1.0
    duration_discount: float = 1.0


class PricingResponse(BaseModel):
    """Dynamic pricing response"""
    vehicle_id: str
    base_daily_rate: float
    predicted_daily_rate: float
    total_price: float
    duration_days: int
    factors: PricingFactors
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "vehicle_id": "vehicle_123",
                "base_daily_rate": 200.0,
                "predicted_daily_rate": 220.0,
                "total_price": 1100.0,
                "duration_days": 5,
                "factors": {
                    "base_rate": 200.0,
                    "weather_factor": 1.1,
                    "competitor_factor": 1.0,
                    "demand_factor": 1.05,
                    "seasonal_factor": 1.0,
                    "duration_discount": 0.95
                }
            }
        }


class CompetitorPriceResponse(BaseModel):
    """Competitor price data"""
    provider: str
    city: str
    category: str
    price: float
    scraped_at: str


class PricingLogResponse(BaseModel):
    """Pricing calculation log"""
    vehicle_id: str
    request_time: str
    base_rate: float
    predicted_rate: float
    weather_factor: float
    competitor_factor: float
