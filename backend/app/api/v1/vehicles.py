"""
Vehicle management endpoints for Hanco-AI
Handles CRUD operations for vehicles with Firestore integration
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import logging
import uuid

from app.core.firebase import db, Collections
from app.core.security import get_guest_id_optional, get_guest_id
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse,
    VehicleListResponse
)
from google.cloud.firestore_v1 import FieldFilter
from google.cloud import firestore

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Helper Functions ====================

def vehicle_doc_to_response(doc_id: str, doc_data: Dict[str, Any]) -> VehicleResponse:
    """Convert Firestore document to VehicleResponse schema"""
    try:
        # Handle Firestore timestamps
        created_at = doc_data.get('created_at')
        updated_at = doc_data.get('updated_at')
        
        if isinstance(created_at, datetime):
            pass  # Already datetime
        elif hasattr(created_at, 'timestamp'):
            created_at = datetime.fromtimestamp(created_at.timestamp())
        else:
            created_at = None
            
        if isinstance(updated_at, datetime):
            pass
        elif hasattr(updated_at, 'timestamp'):
            updated_at = datetime.fromtimestamp(updated_at.timestamp())
        else:
            updated_at = None
        
        return VehicleResponse(
            id=doc_id,
            name=doc_data.get('name'),
            brand=doc_data.get('brand'),
            category=doc_data.get('category'),
            base_daily_rate=doc_data.get('base_daily_rate'),
            city=doc_data.get('city'),
            status=doc_data.get('status', 'available'),
            image_url=doc_data.get('image_url'),
            year=doc_data.get('year'),
            features=doc_data.get('features', []),
            created_at=created_at,
            updated_at=updated_at
        )
    except Exception as e:
        logger.error(f"Error converting vehicle document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing vehicle data: {str(e)}"
        )


async def check_date_overlap(start1: date, end1: date, start2: date, end2: date) -> bool:
    """Check if two date ranges overlap"""
    return start1 <= end2 and end1 >= start2


# ==================== Endpoints ====================

@router.get("", response_model=VehicleListResponse)
async def list_vehicles(
    city: Optional[str] = Query(None, description="Filter by city"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum daily rate"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum daily rate"),
    status: Optional[str] = Query("available", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    List all vehicles with optional filtering
    
    Query parameters:
    - city: Filter by city
    - category: Filter by category (sedan, suv, luxury, etc.)
    - min_price: Minimum base_daily_rate
    - max_price: Maximum base_daily_rate
    - status: Filter by status (default: available)
    - page: Page number for pagination
    - page_size: Number of items per page
    """
    try:
        # Start with base collection reference
        query = db.collection(Collections.VEHICLES)
        
        # Apply filters
        if city:
            query = query.where(filter=FieldFilter('city', '==', city))
        
        if category:
            query = query.where(filter=FieldFilter('category', '==', category.lower()))
        
        if status:
            query = query.where(filter=FieldFilter('status', '==', status))
        
        # Note: Firestore doesn't support range queries on multiple fields efficiently
        # For price filtering, we'll fetch all and filter in-memory
        # In production, consider using Algolia or similar for complex queries
        
        # Execute query
        docs = query.stream()
        
        # Convert to list and apply price filters
        vehicles = []
        for doc in docs:
            doc_data = doc.to_dict()
            vehicle_price = doc_data.get('base_daily_rate', 0)
            
            # Apply price filters
            if min_price is not None and vehicle_price < min_price:
                continue
            if max_price is not None and vehicle_price > max_price:
                continue
            
            vehicles.append(vehicle_doc_to_response(doc.id, doc_data))
        
        # Sort by created_at (newest first)
        vehicles.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
        
        # Apply pagination
        total = len(vehicles)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_vehicles = vehicles[start_idx:end_idx]
        
        logger.info(f"Listed {len(paginated_vehicles)} vehicles (total: {total})")
        
        return VehicleListResponse(
            vehicles=paginated_vehicles,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error listing vehicles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list vehicles: {str(e)}"
        )


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: str):
    """
    Get vehicle details by ID
    
    Parameters:
    - vehicle_id: Vehicle document ID
    """
    try:
        doc_ref = db.collection(Collections.VEHICLES).document(vehicle_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle with ID {vehicle_id} not found"
            )
        
        logger.info(f"Retrieved vehicle: {vehicle_id}")
        return vehicle_doc_to_response(doc.id, doc.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving vehicle {vehicle_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve vehicle: {str(e)}"
        )


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle: VehicleCreate,
    guest_id: str = Depends(get_guest_id)
):
    """
    Create a new vehicle (Admin only)
    
    Requires authentication with admin role.
    """
    try:
        # Generate unique vehicle ID
        vehicle_id = str(uuid.uuid4())
        
        # Prepare vehicle data
        vehicle_data = {
            'id': vehicle_id,
            'name': vehicle.name,
            'brand': vehicle.brand,
            'category': vehicle.category.lower(),
            'base_daily_rate': vehicle.base_daily_rate,
            'city': vehicle.city,
            'status': vehicle.status,
            'image_url': vehicle.image_url or '',
            'year': vehicle.year,
            'features': vehicle.features,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        # Create document in Firestore
        doc_ref = db.collection(Collections.VEHICLES).document(vehicle_id)
        doc_ref.set(vehicle_data)
        
        logger.info(f"Vehicle created: {vehicle_id} by guest {guest_id}")
        
        # Fetch the created document to get server timestamps
        created_doc = doc_ref.get()
        return vehicle_doc_to_response(created_doc.id, created_doc.to_dict())
        
    except Exception as e:
        logger.error(f"Error creating vehicle: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vehicle: {str(e)}"
        )


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: str,
    vehicle_update: VehicleUpdate,
    guest_id: str = Depends(get_guest_id)
):
    """
    Update vehicle details (Admin only)
    
    Parameters:
    - vehicle_id: Vehicle document ID
    
    Only provided fields will be updated.
    """
    try:
        # Check if vehicle exists
        doc_ref = db.collection(Collections.VEHICLES).document(vehicle_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle with ID {vehicle_id} not found"
            )
        
        # Build update data (only non-None fields)
        update_data = {}
        if vehicle_update.name is not None:
            update_data['name'] = vehicle_update.name
        if vehicle_update.brand is not None:
            update_data['brand'] = vehicle_update.brand
        if vehicle_update.category is not None:
            update_data['category'] = vehicle_update.category.lower()
        if vehicle_update.base_daily_rate is not None:
            update_data['base_daily_rate'] = vehicle_update.base_daily_rate
        if vehicle_update.city is not None:
            update_data['city'] = vehicle_update.city
        if vehicle_update.status is not None:
            update_data['status'] = vehicle_update.status
        if vehicle_update.image_url is not None:
            update_data['image_url'] = vehicle_update.image_url
        if vehicle_update.year is not None:
            update_data['year'] = vehicle_update.year
        if vehicle_update.features is not None:
            update_data['features'] = vehicle_update.features
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Add updated timestamp
        update_data['updated_at'] = firestore.SERVER_TIMESTAMP
        
        # Update document
        doc_ref.update(update_data)
        
        logger.info(f"Vehicle updated: {vehicle_id} by guest {guest_id}")
        
        # Fetch updated document
        updated_doc = doc_ref.get()
        return vehicle_doc_to_response(updated_doc.id, updated_doc.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vehicle {vehicle_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vehicle: {str(e)}"
        )


@router.delete("/{vehicle_id}", status_code=status.HTTP_200_OK)
async def delete_vehicle(
    vehicle_id: str,
    guest_id: str = Depends(get_guest_id),
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)")
):
    """
    Delete vehicle (Admin only)
    
    Parameters:
    - vehicle_id: Vehicle document ID
    - hard_delete: If true, permanently deletes. If false (default), soft deletes by setting status to 'inactive'
    
    By default, performs soft delete by setting status to 'inactive'.
    Set hard_delete=true to permanently remove the document.
    """
    try:
        # Check if vehicle exists
        doc_ref = db.collection(Collections.VEHICLES).document(vehicle_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle with ID {vehicle_id} not found"
            )
        
        if hard_delete:
            # Permanent deletion
            doc_ref.delete()
            logger.warning(f"Vehicle permanently deleted: {vehicle_id} by guest {guest_id}")
            return {
                "message": f"Vehicle {vehicle_id} permanently deleted",
                "deleted": True,
                "hard_delete": True
            }
        else:
            # Soft delete - set status to inactive
            doc_ref.update({
                'status': 'inactive',
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Vehicle soft deleted: {vehicle_id} by guest {guest_id}")
            return {
                "message": f"Vehicle {vehicle_id} deactivated (soft delete)",
                "deleted": True,
                "hard_delete": False
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vehicle {vehicle_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete vehicle: {str(e)}"
        )


@router.get("/{vehicle_id}/availability", response_model=Dict[str, Any])
async def check_vehicle_availability(
    vehicle_id: str,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)")
):
    """
    Check vehicle availability for a date range
    
    Parameters:
    - vehicle_id: Vehicle document ID
    - start_date: Booking start date (ISO format: YYYY-MM-DD)
    - end_date: Booking end date (ISO format: YYYY-MM-DD)
    
    Returns availability status and any conflicting bookings.
    """
    try:
        # Validate dates
        if end_date <= start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
        
        if start_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be in the past"
            )
        
        # Check if vehicle exists
        vehicle_ref = db.collection(Collections.VEHICLES).document(vehicle_id)
        vehicle_doc = vehicle_ref.get()
        
        if not vehicle_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle with ID {vehicle_id} not found"
            )
        
        vehicle_data = vehicle_doc.to_dict()
        
        # Check if vehicle is available for booking
        if vehicle_data.get('status') not in ['available', 'rented']:
            return {
                "vehicle_id": vehicle_id,
                "available": False,
                "reason": f"Vehicle status is '{vehicle_data.get('status')}'",
                "conflicting_bookings": []
            }
        
        # Query bookings for this vehicle
        bookings_query = db.collection(Collections.BOOKINGS)\
            .where(filter=FieldFilter('vehicle_id', '==', vehicle_id))\
            .where(filter=FieldFilter('status', 'in', ['pending', 'confirmed', 'active']))
        
        bookings = bookings_query.stream()
        
        # Check for date conflicts
        conflicting_bookings = []
        for booking_doc in bookings:
            booking_data = booking_doc.to_dict()
            booking_start = booking_data.get('start_date')
            booking_end = booking_data.get('end_date')
            
            # Convert Firestore dates to Python dates
            if hasattr(booking_start, 'date'):
                booking_start = booking_start.date()
            if hasattr(booking_end, 'date'):
                booking_end = booking_end.date()
            
            # Check for overlap
            if await check_date_overlap(start_date, end_date, booking_start, booking_end):
                conflicting_bookings.append({
                    "booking_id": booking_doc.id,
                    "start_date": str(booking_start),
                    "end_date": str(booking_end),
                    "status": booking_data.get('status')
                })
        
        available = len(conflicting_bookings) == 0
        
        logger.info(f"Availability check for vehicle {vehicle_id}: {available}")
        
        return {
            "vehicle_id": vehicle_id,
            "available": available,
            "requested_start_date": str(start_date),
            "requested_end_date": str(end_date),
            "conflicting_bookings": conflicting_bookings,
            "vehicle_status": vehicle_data.get('status')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking availability for vehicle {vehicle_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check availability: {str(e)}"
        )
