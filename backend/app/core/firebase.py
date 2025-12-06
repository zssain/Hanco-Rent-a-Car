"""
Firebase integration for Hanco-AI
Firestore database and Firebase Authentication
"""
import firebase_admin
from firebase_admin import credentials, firestore, auth
from typing import Optional, Dict, Any, List
import logging
from functools import lru_cache
import json
import os
import base64

from app.core.config import settings

logger = logging.getLogger(__name__)


class FirebaseClient:
    """Firebase Admin SDK client singleton"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Priority 1: Load from Base64 encoded environment variable (safest for production)
            firebase_creds_b64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_B64")
            
            if firebase_creds_b64:
                logger.info("Loading Firebase credentials from Base64 environment variable")
                cred_json = base64.b64decode(firebase_creds_b64).decode('utf-8')
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
            else:
                # Priority 2: Load from JSON environment variable
                firebase_creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
                
                if firebase_creds_json:
                    logger.info("Loading Firebase credentials from JSON environment variable")
                    cred_dict = json.loads(firebase_creds_json)
                    cred = credentials.Certificate(cred_dict)
                else:
                    # Priority 3: Load from file path (for local development)
                    logger.info(f"Loading Firebase credentials from file: {settings.FIREBASE_CREDENTIALS_PATH}")
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            
            # Initialize Firebase app
            firebase_admin.initialize_app(cred, {
                'projectId': settings.FIREBASE_PROJECT_ID,
            })
            
            # Initialize Firestore client
            self._db = firestore.client()
            
            logger.info(f"✅ Firebase initialized successfully for project: {settings.FIREBASE_PROJECT_ID}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase: {e}")
            raise
    
    @property
    def db(self) -> firestore.Client:
        """Get Firestore client instance"""
        return self._db
    
    @property
    def auth_client(self):
        """Get Firebase Auth client"""
        return auth


# Global Firebase client instance
firebase_client = FirebaseClient()
db = firebase_client.db
auth_client = firebase_client.auth_client


# ==================== Collection References ====================
class Collections:
    """Firestore collection names"""
    USERS = "users"
    VEHICLES = "vehicles"
    BOOKINGS = "bookings"
    CHAT_SESSIONS = "chat_sessions"
    CHAT_MESSAGES = "chat_messages"
    PAYMENTS = "payments"
    COMPETITORS = "competitor_prices"
    PRICING_LOGS = "pricing_logs"


# ==================== Authentication Functions ====================

def verify_id_token(token: str) -> Dict[str, Any]:
    """
    Verify Firebase ID token and return decoded claims.
    
    Args:
        token: Firebase ID token from client
        
    Returns:
        Decoded token claims including uid, email, etc.
        
    Raises:
        ValueError: If token is invalid or expired
    """
    try:
        decoded_token = auth_client.verify_id_token(token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise ValueError("Invalid ID token")
    except auth.ExpiredIdTokenError:
        raise ValueError("Token has expired")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise ValueError(f"Token verification failed: {str(e)}")


def get_user(uid: str) -> Optional[Dict[str, Any]]:
    """
    Get user data from Firestore by UID.
    
    Args:
        uid: Firebase user UID
        
    Returns:
        User document data or None if not found
    """
    try:
        user_ref = db.collection(Collections.USERS).document(uid)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            return user_doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error fetching user {uid}: {e}")
        return None


def create_user(email: str, password: str, **kwargs) -> Dict[str, Any]:
    """
    Create a new Firebase user and store in Firestore.
    
    Args:
        email: User email
        password: User password
        **kwargs: Additional user data (name, phone, role, etc.)
        
    Returns:
        Created user data including uid
        
    Raises:
        ValueError: If user creation fails
    """
    try:
        # Create Firebase Auth user
        user_record = auth_client.create_user(
            email=email,
            password=password,
            email_verified=False
        )
        
        # Prepare user document data
        user_data = {
            'uid': user_record.uid,
            'email': email,
            'name': kwargs.get('name', ''),
            'phone': kwargs.get('phone', ''),
            'role': kwargs.get('role', 'consumer'),
            'is_active': True,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        # Store in Firestore
        db.collection(Collections.USERS).document(user_record.uid).set(user_data)
        
        # Set custom claims for role-based access
        auth_client.set_custom_user_claims(user_record.uid, {'role': user_data['role']})
        
        logger.info(f"✅ User created successfully: {email}")
        
        return user_data
        
    except auth.EmailAlreadyExistsError:
        raise ValueError("Email already exists")
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise ValueError(f"User creation failed: {str(e)}")


def update_user(uid: str, data: Dict[str, Any]) -> bool:
    """
    Update user data in Firestore.
    
    Args:
        uid: User UID
        data: Dictionary of fields to update
        
    Returns:
        True if successful
    """
    try:
        data['updated_at'] = firestore.SERVER_TIMESTAMP
        db.collection(Collections.USERS).document(uid).update(data)
        return True
    except Exception as e:
        logger.error(f"Error updating user {uid}: {e}")
        return False


def delete_user(uid: str) -> bool:
    """
    Delete user from Firebase Auth and Firestore.
    
    Args:
        uid: User UID
        
    Returns:
        True if successful
    """
    try:
        # Delete from Firebase Auth
        auth_client.delete_user(uid)
        
        # Delete from Firestore
        db.collection(Collections.USERS).document(uid).delete()
        
        logger.info(f"✅ User deleted: {uid}")
        return True
    except Exception as e:
        logger.error(f"Error deleting user {uid}: {e}")
        return False


# ==================== Firestore Helper Functions ====================

def get_document(collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """Get a document from Firestore by ID"""
    try:
        doc_ref = db.collection(collection).document(doc_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None
    except Exception as e:
        logger.error(f"Error getting document {collection}/{doc_id}: {e}")
        return None


def create_document(collection: str, data: Dict[str, Any], doc_id: Optional[str] = None) -> Optional[str]:
    """
    Create a new document in Firestore.
    
    Returns:
        Document ID if successful, None otherwise
    """
    try:
        data['created_at'] = firestore.SERVER_TIMESTAMP
        data['updated_at'] = firestore.SERVER_TIMESTAMP
        
        if doc_id:
            db.collection(collection).document(doc_id).set(data)
            return doc_id
        else:
            doc_ref = db.collection(collection).add(data)
            return doc_ref[1].id
    except Exception as e:
        logger.error(f"Error creating document in {collection}: {e}")
        return None


def update_document(collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
    """Update a document in Firestore"""
    try:
        data['updated_at'] = firestore.SERVER_TIMESTAMP
        db.collection(collection).document(doc_id).update(data)
        return True
    except Exception as e:
        logger.error(f"Error updating document {collection}/{doc_id}: {e}")
        return False


def delete_document(collection: str, doc_id: str) -> bool:
    """Delete a document from Firestore"""
    try:
        db.collection(collection).document(doc_id).delete()
        return True
    except Exception as e:
        logger.error(f"Error deleting document {collection}/{doc_id}: {e}")
        return False


def query_documents(
    collection: str,
    filters: Optional[List[tuple]] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Query documents from Firestore with filters.
    
    Args:
        collection: Collection name
        filters: List of tuples (field, operator, value)
        order_by: Field to order by
        limit: Maximum number of results
        
    Returns:
        List of documents
    """
    try:
        query = db.collection(collection)
        
        # Apply filters
        if filters:
            for field, operator, value in filters:
                query = query.where(field, operator, value)
        
        # Apply ordering
        if order_by:
            query = query.order_by(order_by)
        
        # Apply limit
        if limit:
            query = query.limit(limit)
        
        # Execute query
        docs = query.stream()
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(data)
        
        return results
    except Exception as e:
        logger.error(f"Error querying {collection}: {e}")
        return []
