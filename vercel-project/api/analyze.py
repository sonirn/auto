"""Video analysis API endpoint for Vercel"""
import json
import sys
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler

# Add lib directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from database import get_collection, PROJECT_STATUS
from auth import auth_service
from video_analysis import VideoAnalysisService

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle video analysis request"""
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
            
            # Check if sample video exists
            sample_video_path = project.get('sample_video_path')
            if not sample_video_path:
                self.send_error(400, "No sample video uploaded")
                return
            
            # Update project status
            collection.update_one(
                {"_id": project_id},
                {"$set": {
                    "status": PROJECT_STATUS["ANALYZING"],
                    "progress": 10.0,
                    "updated_at": datetime.utcnow().isoformat()
                }}
            )
            
            # Initialize video analysis service
            analysis_service = VideoAnalysisService()
            
            # Perform analysis
            analysis_result = analysis_service.analyze_video(
                video_path=sample_video_path,
                character_image_path=project.get('character_image_path'),
                audio_path=project.get('audio_path')
            )
            
            # Update project with analysis results
            update_data = {
                "status": PROJECT_STATUS["PLANNING"],
                "progress": 50.0,
                "video_analysis": analysis_result.get('video_analysis', {}),
                "generation_plan": analysis_result.get('generation_plan', {}),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            collection.update_one(
                {"_id": project_id},
                {"$set": update_data}
            )
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "message": "Video analysis completed successfully",
                "analysis": analysis_result,
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