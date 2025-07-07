"""
Minimal FastAPI server for Vercel deployment
Only includes essential endpoints for basic functionality
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

# Basic models
class AuthRequest(BaseModel):
    email: str
    password: str

class ProjectResponse(BaseModel):
    id: str
    status: str
    created_at: datetime
    message: str

# Initialize FastAPI app
app = FastAPI(
    title="AI Video Generation API - Minimal",
    description="Minimal API for Vercel deployment",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple database connection check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Minimal API is running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/database/status")
async def get_database_status():
    """Get database connection status"""
    try:
        # Simple PostgreSQL connection test
        import psycopg2
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return {
                "available": False,
                "error": "DATABASE_URL environment variable not set"
            }
        
        # Test connection
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version(), current_database(), current_user")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            "available": True,
            "database_info": {
                "version": result[0],
                "database": result[1],
                "user": result[2],
                "status": "connected"
            }
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }

@app.post("/api/projects")
async def create_project():
    """Create a new video project"""
    try:
        project_id = str(uuid.uuid4())
        return ProjectResponse(
            id=project_id,
            status="created",
            created_at=datetime.utcnow(),
            message="Project created successfully (minimal mode)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project details"""
    return {
        "id": project_id,
        "status": "ready",
        "created_at": datetime.utcnow().isoformat(),
        "progress": 0,
        "message": "Minimal API - project tracking"
    }

@app.post("/api/auth/register")
async def register_user(auth_request: AuthRequest):
    """Register a new user (minimal implementation)"""
    try:
        user_id = str(uuid.uuid4())
        return {
            "user_id": user_id,
            "email": auth_request.email,
            "message": "User registered successfully (minimal mode)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/env/check")
async def check_environment():
    """Check environment variables"""
    env_vars = [
        "DATABASE_URL",
        "GROQ_API_KEY", 
        "RUNWAYML_API_KEY",
        "GEMINI_API_KEY"
    ]
    
    status = {}
    for var in env_vars:
        value = os.environ.get(var)
        status[var] = "✓ Set" if value else "✗ Missing"
    
    return {
        "environment_check": status,
        "timestamp": datetime.utcnow().isoformat()
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Video Generation API - Minimal Version",
        "status": "running",
        "version": "1.0.0",
        "endpoints": [
            "/api/health",
            "/api/database/status",
            "/api/projects",
            "/api/auth/register",
            "/api/env/check"
        ]
    }

# Export app for Vercel
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)