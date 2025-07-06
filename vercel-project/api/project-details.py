"""Project details API endpoint for Vercel"""
import json
import sys
import os
from http.server import BaseHTTPRequestHandler

# Add lib directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from database import get_collection
from auth import auth_service

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle project details request"""
        try:
            # Get authorization header
            auth_header = self.headers.get('Authorization')
            user_id = auth_service.get_current_user(auth_header)
            
            if not user_id:
                self.send_error(401, "Authentication required")
                return
            
            # Get project ID from URL path
            path_parts = self.path.split('/')
            if len(path_parts) < 3:
                self.send_error(400, "Project ID required")
                return
            
            project_id = path_parts[2]
            
            # Get project from database
            collection = get_collection('video_projects')
            project = collection.find_one({"_id": project_id, "user_id": user_id})
            
            if not project:
                self.send_error(404, "Project not found")
                return
            
            # Convert ObjectId to string for JSON serialization
            project['_id'] = str(project['_id'])
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(project).encode())
            
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()