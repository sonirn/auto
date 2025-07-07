#!/usr/bin/env python3
import sys
import os
import uuid
from datetime import datetime

# Add the backend directory to the path
sys.path.append('/app/backend')

# Set the DATABASE_URL environment variable
os.environ['DATABASE_URL'] = "postgres://neondb_owner:npg_2RNt5IwBXShV@ep-muddy-cell-a4gezv5f-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Import the database module
from database import db, init_database

async def create_test_user():
    """Create a test user in the database"""
    try:
        # Initialize the database
        init_database()
        
        # Create a test user
        user_id = "00000000-0000-0000-0000-000000000001"
        user_data = {
            "id": user_id,
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
            "projects": [],
            "subscription_status": "free"
        }
        
        # Insert the user
        await db.users.insert_one(user_data)
        
        print(f"Created test user with ID: {user_id}")
        return user_id
    except Exception as e:
        print(f"Error creating test user: {str(e)}")
        return None

if __name__ == "__main__":
    import asyncio
    asyncio.run(create_test_user())