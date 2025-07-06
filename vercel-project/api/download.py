"""Video download API endpoint for Vercel"""
import json
import sys
import os
import base64
from http.server import BaseHTTPRequestHandler

# Add lib directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from database import get_collection
from auth import auth_service
from cloud_storage import cloud_storage_service

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle video download request"""
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
            
            # Check if video is ready
            if project.get('status') != 'completed':
                self.send_error(400, "Video not ready for download")
                return
            
            # Get video path
            video_path = project.get('generated_video_path')
            if not video_path:
                self.send_error(400, "No generated video available")
                return
            
            # Download video from cloud storage
            video_content = cloud_storage_service.download_file(video_path)
            
            # Convert to base64 for JSON response
            video_base64 = base64.b64encode(video_content).decode()
            
            # Update download count
            collection.update_one(
                {"_id": project_id},
                {"$inc": {"download_count": 1}}
            )
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "video_base64": video_base64,
                "filename": f"generated_video_{project_id}.mp4",
                "content_type": "video/mp4",
                "project_id": project_id
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()