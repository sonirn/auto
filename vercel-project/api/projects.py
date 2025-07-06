"""Projects API endpoints for Vercel"""
import json
import uuid
from datetime import datetime
from typing import Optional
from http.server import BaseHTTPRequestHandler
import sys
import os

# Add lib directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from database import get_collection, PROJECT_STATUS
from auth import auth_service

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests - list projects"""
        try:
            # Get authorization header
            auth_header = self.headers.get('Authorization')
            user_id = auth_service.get_current_user(auth_header)
            
            if not user_id:
                self.send_error(401, "Authentication required")
                return
            
            # Get projects collection
            collection = get_collection('video_projects')
            
            # Find user's projects
            projects = list(collection.find({"user_id": user_id}))
            
            # Convert ObjectId to string for JSON serialization
            for project in projects:
                project['_id'] = str(project['_id'])
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {"projects": projects}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests - create project"""
        try:
            # Get authorization header
            auth_header = self.headers.get('Authorization')
            user_id = auth_service.get_current_user(auth_header)
            
            if not user_id:
                self.send_error(401, "Authentication required")
                return
            
            # Create new project
            project_id = str(uuid.uuid4())
            project_data = {
                "_id": project_id,
                "user_id": user_id,
                "status": PROJECT_STATUS["UPLOADING"],
                "created_at": datetime.utcnow().isoformat(),
                "progress": 0.0,
                "estimated_time_remaining": 0,
                "download_count": 0
            }
            
            # Save to database
            collection = get_collection('video_projects')
            collection.insert_one(project_data)
            
            # Send response
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(project_data).encode())
            
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_DELETE(self):
        """Handle DELETE requests - delete project"""
        try:
            # Get authorization header
            auth_header = self.headers.get('Authorization')
            user_id = auth_service.get_current_user(auth_header)
            
            if not user_id:
                self.send_error(401, "Authentication required")
                return
            
            # Extract project ID from path
            path_parts = self.path.split('/')
            if len(path_parts) < 3:
                self.send_error(400, "Project ID required")
                return
            
            project_id = path_parts[2]
            
            # Delete project
            collection = get_collection('video_projects')
            result = collection.delete_one({"_id": project_id, "user_id": user_id})
            
            if result.deleted_count == 0:
                self.send_error(404, "Project not found")
                return
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {"message": "Project deleted successfully"}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()