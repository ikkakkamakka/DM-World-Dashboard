#!/usr/bin/env python3
"""
Data migration script to add owner_id to existing data and create default admin user
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def migrate_data():
    # Database connections
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    
    # Main database
    db = client[os.environ['DB_NAME']]
    # Users database
    users_db = client[f"{os.environ['DB_NAME']}_users"]
    
    print("🚀 Starting data migration...")
    
    # Step 1: Create default admin user
    admin_username = "admin"
    admin_email = "admin@campaign.manager"
    admin_password = "admin123"  # Should be changed after first login
    
    # Check if admin user already exists
    existing_admin = await users_db.users.find_one({"username": admin_username})
    
    if not existing_admin:
        admin_user = {
            "id": str(uuid.uuid4()),
            "username": admin_username,
            "email": admin_email,
            "password_hash": pwd_context.hash(admin_password),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        await users_db.users.insert_one(admin_user)
        admin_id = admin_user["id"]
        print(f"✅ Created admin user: {admin_username} (ID: {admin_id})")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password} (Please change after first login)")
    else:
        admin_id = existing_admin["id"]
        print(f"✅ Admin user already exists: {admin_username} (ID: {admin_id})")
    
    # Step 2: Update existing kingdoms to have owner_id
    kingdoms_result = await db.multi_kingdoms.update_many(
        {"owner_id": {"$exists": False}},
        {"$set": {"owner_id": admin_id}}
    )
    print(f"✅ Updated {kingdoms_result.modified_count} kingdoms with owner_id")
    
    # Step 3: Update existing events
    events_result = await db.events.update_many(
        {"owner_id": {"$exists": False}},
        {"$set": {"owner_id": admin_id}}
    )
    print(f"✅ Updated {events_result.modified_count} events with owner_id")
    
    # Step 4: Update existing calendar events
    calendar_events_result = await db.calendar_events.update_many(
        {"owner_id": {"$exists": False}},
        {"$set": {"owner_id": admin_id}}
    )
    print(f"✅ Updated {calendar_events_result.modified_count} calendar events with owner_id")
    
    # Step 5: Update existing kingdom boundaries
    boundaries_result = await db.kingdom_boundaries.update_many(
        {"owner_id": {"$exists": False}},
        {"$set": {"owner_id": admin_id}}
    )
    print(f"✅ Updated {boundaries_result.modified_count} kingdom boundaries with owner_id")
    
    print("\n🎉 Data migration completed successfully!")
    print("\nNext steps:")
    print("1. Login as admin user to access existing data")
    print("2. Create new DM accounts for testing")
    print("3. Change admin password after first login")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_data())