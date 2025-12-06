"""
Booking model for Firestore
Represents booking documents in bookings collection
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Dict, Any
from google.cloud.firestore_v1 import DocumentSnapshot


@dataclass
class Booking:
    """Booking model for Firestore storage"""
    
    id: str
    user_id: str
    vehicle_id: str
    start_date: date
    end_date: date
    total_price: float
    status: str = "pending"  # pending, confirmed, active, completed, cancelled
    payment_status: str = "pending"  # pending, completed, refunded, failed
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_firestore(self) -> Dict[str, Any]:
        """Convert model to Firestore-compatible dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'vehicle_id': self.vehicle_id,
            'start_date': self.start_date.isoformat() if isinstance(self.start_date, date) else self.start_date,
            'end_date': self.end_date.isoformat() if isinstance(self.end_date, date) else self.end_date,
            'total_price': self.total_price,
            'status': self.status,
            'payment_status': self.payment_status,
        }
        
        if self.created_at:
            data['created_at'] = self.created_at
        if self.updated_at:
            data['updated_at'] = self.updated_at
            
        return data
    
    @classmethod
    def from_firestore(cls, doc: DocumentSnapshot) -> Optional['Booking']:
        """Create Booking instance from Firestore document"""
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        
        # Parse dates
        start_date = data.get('start_date')
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date).date()
        
        end_date = data.get('end_date')
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date).date()
        
        return cls(
            id=data.get('id', doc.id),
            user_id=data.get('user_id', ''),
            vehicle_id=data.get('vehicle_id', ''),
            start_date=start_date,
            end_date=end_date,
            total_price=data.get('total_price', 0.0),
            status=data.get('status', 'pending'),
            payment_status=data.get('payment_status', 'pending'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def validate_status(self) -> bool:
        """Validate booking status"""
        valid_statuses = ['pending', 'confirmed', 'active', 'completed', 'cancelled']
        return self.status in valid_statuses
    
    def validate_payment_status(self) -> bool:
        """Validate payment status"""
        valid_statuses = ['pending', 'completed', 'refunded', 'failed']
        return self.payment_status in valid_statuses
    
    def validate_dates(self) -> bool:
        """Validate booking dates"""
        return self.end_date > self.start_date
    
    def get_duration_days(self) -> int:
        """Calculate booking duration in days"""
        return (self.end_date - self.start_date).days
