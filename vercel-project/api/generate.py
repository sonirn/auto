"""Video generation API endpoint for Vercel"""
import json
import sys
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler

# Add lib directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from database import get_collection, PROJECT_STATUS
from auth import auth_service
from video_generation import VideoGenerationService, VideoModel

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle video generation request"""
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
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                try:
                    request_data = json.loads(post_data.decode())
                    selected_model = request_data.get('model', 'runwayml_gen4')
                except:
                    selected_model = 'runwayml_gen4'
            else:
                selected_model = 'runwayml_gen4'
            
            # Get project from database
            collection = get_collection('video_projects')
            project = collection.find_one({"_id": project_id, "user_id": user_id})
            
            if not project:
                self.send_error(404, "Project not found")
                return
            
            # Check if generation plan exists
            generation_plan = project.get('generation_plan')
            if not generation_plan:
                self.send_error(400, "No generation plan available. Please analyze video first.")
                return
            
            # Update project status
            collection.update_one(
                {"_id": project_id},
                {"$set": {
                    "status": PROJECT_STATUS["GENERATING"],
                    "progress": 60.0,
                    "selected_model": selected_model,
                    "updated_at": datetime.utcnow().isoformat()
                }}
            )
            
            # Initialize video generation service
            generation_service = VideoGenerationService()
            
            # Convert model string to enum
            model_mapping = {
                'runwayml_gen4': VideoModel.RUNWAYML_GEN4,
                'runwayml_gen3': VideoModel.RUNWAYML_GEN3,
                'google_veo2': VideoModel.GOOGLE_VEO2,
                'google_veo3': VideoModel.GOOGLE_VEO3
            }
            
            model_enum = model_mapping.get(selected_model, VideoModel.RUNWAYML_GEN4)
            
            # Start generation
            generation_result = generation_service.generate_video(
                project_id=project_id,
                generation_plan=generation_plan,
                model=model_enum
            )
            
            # Update project with generation info
            update_data = {
                "status": PROJECT_STATUS["PROCESSING"],
                "progress": 70.0,
                "generation_id": generation_result.get('generation_id'),
                "estimated_time_remaining": generation_result.get('estimated_time', 120),
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
                "message": "Video generation started successfully",
                "generation_id": generation_result.get('generation_id'),
                "model": selected_model,
                "estimated_time": generation_result.get('estimated_time', 120),
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