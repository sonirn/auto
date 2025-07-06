"""Audio upload API endpoint for Vercel"""
import json
import base64
import sys
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler

# Add lib directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from database import get_collection
from auth import auth_service
from cloud_storage import cloud_storage_service

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle audio upload"""
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
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "No file data provided")
                return
            
            post_data = self.rfile.read(content_length)
            
            # Parse multipart form data (simplified)
            try:
                # For now, assume the file is sent as base64 in JSON
                request_data = json.loads(post_data.decode())
                file_data = base64.b64decode(request_data.get('file_data', ''))
                filename = request_data.get('filename', 'audio.mp3')
                content_type = request_data.get('content_type', 'audio/mpeg')
            except:
                # Fallback: treat as raw file data
                file_data = post_data
                filename = 'audio.mp3'
                content_type = 'audio/mpeg'
            
            # Validate file type
            allowed_types = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/aac']
            if content_type not in allowed_types:
                self.send_error(400, "Invalid file type. Only audio files are allowed.")
                return
            
            # Validate file size (max 25MB)
            max_size = 25 * 1024 * 1024  # 25MB
            if len(file_data) > max_size:
                self.send_error(400, "File too large. Maximum size is 25MB.")
                return
            
            # Upload to cloud storage
            file_url = cloud_storage_service.upload_file(
                content=file_data,
                user_id=user_id,
                project_id=project_id,
                folder='input',
                filename=filename,
                content_type=content_type
            )
            
            # Update project in database
            collection = get_collection('video_projects')
            update_data = {
                "audio_path": file_url,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = collection.update_one(
                {"_id": project_id, "user_id": user_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                self.send_error(404, "Project not found")
                return
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "message": "Audio uploaded successfully",
                "file_url": file_url,
                "project_id": project_id
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()