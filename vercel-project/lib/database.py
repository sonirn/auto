"""Database utilities for Vercel serverless functions"""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Global database client
_client: Optional[AsyncIOMotorClient] = None
_database = None

def get_database():
    """Get MongoDB database instance"""
    global _client, _database
    
    if _database is None:
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'video_generation_db')
        
        _client = AsyncIOMotorClient(mongo_url)
        _database = _client[db_name]
        
        logger.info(f"Connected to MongoDB: {db_name}")
    
    return _database

async def get_collection(collection_name: str):
    """Get MongoDB collection"""
    db = get_database()
    return db[collection_name]

async def close_database():
    """Close database connection"""
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("Database connection closed")

# Project status constants
PROJECT_STATUS = {
    "UPLOADING": "uploading",
    "ANALYZING": "analyzing", 
    "PLANNING": "planning",
    "GENERATING": "generating",
    "PROCESSING": "processing",
    "COMPLETED": "completed",
    "FAILED": "failed"
}