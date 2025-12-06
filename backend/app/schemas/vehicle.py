"""
Vehicle request/response schemas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class VehicleBase(BaseModel):
    """Base vehicle schema"""
    name: str = Field(..., min_length=2)
    brand: str
    category: str
    base_daily_rate: float = Field(..., gt=0)
    city: str
    image_url: Optional[str] = None
    year: Optional[int] = Field(None, ge=2000, le=2025)
    features: List[str] = Field(default_factory=list)
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = ['sedan', 'suv', 'luxury', 'economy', 'sports', 'van', 'truck']
        if v.lower() not in valid_categories:
            raise ValueError(f'Category must be one of: {", ".join(valid_categories)}')
        return v.lower()


class VehicleCreate(VehicleBase):
    """Create vehicle request"""
    status: str = Field(default="available", pattern=r'^(available|maintenance)$')


class VehicleUpdate(BaseModel):
    """Update vehicle request (all fields optional)"""
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    base_daily_rate: Optional[float] = Field(None, gt=0)
    city: Optional[str] = None
    status: Optional[str] = None
    image_url: Optional[str] = None
    year: Optional[int] = None
    features: Optional[List[str]] = None


class VehicleResponse(VehicleBase):
    """Vehicle response with additional fields"""
    id: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VehicleListResponse(BaseModel):
    """List of vehicles response"""
    vehicles: List[VehicleResponse]
    total: int
    page: int = 1
    page_size: int = 20


class VehicleSearchRequest(BaseModel):
    """Vehicle search/filter request"""
    city: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    status: Optional[str] = "available"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
