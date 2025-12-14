"""
Populate Firebase with branch locations
"""
import sys
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import json
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if already initialized
        try:
            firebase_admin.get_app()
            print("✅ Firebase already initialized")
            return firestore.client()
        except ValueError:
            pass  # Not initialized yet, continue
        
        # Method 1: Try GOOGLE_APPLICATION_CREDENTIALS
        google_creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if google_creds_path:
            print(f"Loading credentials from: {google_creds_path}")
            cred = credentials.Certificate(google_creds_path)
        else:
            # Method 2: Try inline JSON
            firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
            
            if firebase_creds_json:
                print("Loading credentials from FIREBASE_CREDENTIALS_JSON")
                cred_dict = json.loads(firebase_creds_json)
                cred = credentials.Certificate(cred_dict)
            else:
                raise ValueError(
                    "Firebase credentials not found. Please set either:\n"
                    "  - GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-key.json\n"
                    "  - FIREBASE_CREDENTIALS_JSON='{...}'"
                )
        
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully")
        
        return firestore.client()
    except Exception as e:
        print(f"❌ Failed to initialize Firebase: {e}")
        raise

def populate_branches(db):
    """Create branch locations in Firebase"""
    branches = [
        {
            "id": "riyadh_airport",
            "name": "Riyadh King Khalid International Airport",
            "city": "Riyadh",
            "address": "King Khalid International Airport, Exit 5",
            "phone": "+966112345001",
            "latitude": 24.9574,
            "longitude": 46.6983,
            "is_active": True,
            "operating_hours": "24/7",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        },
        {
            "id": "riyadh_olaya",
            "name": "Riyadh Olaya District",
            "city": "Riyadh",
            "address": "Olaya Street, Al Olaya District",
            "phone": "+966112345002",
            "latitude": 24.6979,
            "longitude": 46.6857,
            "is_active": True,
            "operating_hours": "08:00 - 22:00",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        },
        {
            "id": "riyadh_malaz",
            "name": "Riyadh Al Malaz Center",
            "city": "Riyadh",
            "address": "King Abdulaziz Road, Al Malaz",
            "phone": "+966112345003",
            "latitude": 24.6880,
            "longitude": 46.7280,
            "is_active": True,
            "operating_hours": "08:00 - 22:00",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        },
        {
            "id": "jeddah_airport",
            "name": "Jeddah King Abdulaziz International Airport",
            "city": "Jeddah",
            "address": "King Abdulaziz International Airport, Terminal 1",
            "phone": "+966122345001",
            "latitude": 21.6796,
            "longitude": 39.1564,
            "is_active": True,
            "operating_hours": "24/7",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        },
        {
            "id": "jeddah_corniche",
            "name": "Jeddah Corniche",
            "city": "Jeddah",
            "address": "Corniche Road, Al Hamra District",
            "phone": "+966122345002",
            "latitude": 21.5810,
            "longitude": 39.1653,
            "is_active": True,
            "operating_hours": "08:00 - 22:00",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        },
        {
            "id": "jeddah_redsea",
            "name": "Jeddah Red Sea Mall",
            "city": "Jeddah",
            "address": "Red Sea Mall, Al Zahra District",
            "phone": "+966122345003",
            "latitude": 21.6340,
            "longitude": 39.1033,
            "is_active": True,
            "operating_hours": "10:00 - 23:00",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        },
        {
            "id": "dammam_airport",
            "name": "Dammam King Fahd International Airport",
            "city": "Dammam",
            "address": "King Fahd International Airport",
            "phone": "+966132345001",
            "latitude": 26.4714,
            "longitude": 49.7979,
            "is_active": True,
            "operating_hours": "24/7",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        },
        {
            "id": "dammam_corniche",
            "name": "Dammam Corniche",
            "city": "Dammam",
            "address": "King Abdullah Street, Corniche Area",
            "phone": "+966132345002",
            "latitude": 26.4207,
            "longitude": 50.0888,
            "is_active": True,
            "operating_hours": "08:00 - 22:00",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
    ]
    
    print(f"\n📍 Creating {len(branches)} branch locations...")
    print("-" * 70)
    
    batch = db.batch()
    branches_ref = db.collection('branches')
    
    for branch in branches:
        branch_id = branch.pop('id')
        doc_ref = branches_ref.document(branch_id)
        batch.set(doc_ref, branch)
        print(f"✅ {branch['name']} ({branch['city']})")
    
    # Commit the batch
    batch.commit()
    print(f"\n✅ Successfully created {len(branches)} branches!")

def main():
    """Main execution"""
    print("=" * 70)
    print("🚀 HANCO Branch Locations Population")
    print("=" * 70)
    
    # Initialize Firebase
    db = initialize_firebase()
    
    # Populate branches
    populate_branches(db)
    
    # Print summary
    print("\n" + "=" * 70)
    print("✅ Branch Population Complete!")
    print("=" * 70)
    
    print("\n" + "=" * 70)
    print("🔗 Firebase Console:")
    project_id = os.getenv('FIREBASE_PROJECT_ID', 'your-project')
    print(f"   https://console.firebase.google.com/project/{project_id}/firestore")
    print("\n💡 Branches are now available for pickup/dropoff selection!")
    print("=" * 70)

if __name__ == "__main__":
    main()
