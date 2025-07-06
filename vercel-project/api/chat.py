"""Chat API endpoint for Vercel"""
import json
import sys
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import litellm

# Add lib directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from database import get_collection
from auth import auth_service

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle chat request"""
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
                self.send_error(400, "Message is required")
                return
            
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode())
            message = request_data.get('message', '')
            
            if not message:
                self.send_error(400, "Message is required")
                return
            
            # Get project from database
            collection = get_collection('video_projects')
            project = collection.find_one({"_id": project_id, "user_id": user_id})
            
            if not project:
                self.send_error(404, "Project not found")
                return
            
            # Get current generation plan
            generation_plan = project.get('generation_plan', {})
            
            # Create chat context
            context = f"""
            You are an AI assistant helping to modify video generation plans.
            
            Current generation plan:
            {json.dumps(generation_plan, indent=2)}
            
            User message: {message}
            
            Please provide a helpful response about modifying the generation plan.
            If the user wants to change something specific, provide updated plan suggestions.
            Keep your response concise and focused on video generation.
            """
            
            # Call Groq LLM
            groq_api_key = os.environ.get('GROQ_API_KEY')
            if not groq_api_key:
                self.send_error(500, "AI service not configured")
                return
            
            os.environ['GROQ_API_KEY'] = groq_api_key
            
            response = litellm.completion(
                model="groq/llama3-8b-8192",
                messages=[{"role": "user", "content": context}],
                temperature=0.7,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            
            # Update chat history
            chat_history = project.get('chat_history', [])
            chat_history.append({
                "user_message": message,
                "ai_response": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update project in database
            collection.update_one(
                {"_id": project_id},
                {"$set": {
                    "chat_history": chat_history,
                    "updated_at": datetime.utcnow().isoformat()
                }}
            )
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                "message": ai_response,
                "project_id": project_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()