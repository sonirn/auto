"""Video analysis API endpoint for Vercel deployment"""
import json
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def handler(request):
    """Handle video analysis request"""
    try:
        method = request.get('method', 'POST')
        headers = request.get('headers', {})
        query = request.get('query', {})
        body = request.get('body', {})
        
        # Handle CORS
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Content-Type': 'application/json'
        }
        
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        if method != 'POST':
            return {
                'statusCode': 405,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        # Import database
        from database import db
        
        # Get user ID (simplified auth for now)
        user_id = "default_user"
        auth_header = headers.get('authorization') or headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            user_id = "authenticated_user"
        
        # Get project ID from query or body
        project_id = query.get('project_id') or body.get('project_id')
        if not project_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Project ID required'})
            }
        
        # Get project from database
        project = db.video_projects.find_one({"id": project_id, "user_id": user_id})
        
        if not project:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Project not found'})
            }
        
        # Check if sample video exists
        sample_video_path = project.get('sample_video_path')
        if not sample_video_path:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'No sample video uploaded'})
            }
        
        # Update project status
        db.video_projects.update_one(
            {"id": project_id},
            {"$set": {
                "status": "analyzing",
                "progress": 10.0,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Perform video analysis using AI
        try:
            import asyncio
            import litellm
            
            # Use Groq for video analysis
            groq_api_key = os.environ.get('GROQ_API_KEY')
            if not groq_api_key:
                return {
                    'statusCode': 500,
                    'headers': cors_headers,
                    'body': json.dumps({'error': 'AI service not configured'})
                }
            
            # Simple video analysis (in production, use the full VideoAnalysisService)
            analysis_prompt = f"""
            Analyze this video file: {sample_video_path}
            
            Provide a comprehensive analysis including:
            1. Visual elements (scenes, objects, lighting, colors)
            2. Style and mood (genre, pacing, effects)
            3. Technical aspects (quality, resolution estimates)
            4. Content analysis (theme, message)
            
            Then create a generation plan with:
            1. Scene breakdown
            2. Visual requirements
            3. Recommended AI model (RunwayML Gen4 recommended)
            
            Return in JSON format with 'analysis' and 'plan' keys.
            """
            
            # Create event loop for async operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                response = loop.run_until_complete(
                    asyncio.to_thread(
                        litellm.completion,
                        model="groq/llama3-8b-8192",
                        messages=[
                            {"role": "system", "content": "You are an expert video analysis AI."},
                            {"role": "user", "content": analysis_prompt}
                        ],
                        api_key=groq_api_key,
                        temperature=0.7,
                        max_tokens=1500
                    )
                )
                
                response_text = response.choices[0].message.content
                
                # Try to parse JSON response
                try:
                    analysis_result = json.loads(response_text)
                except json.JSONDecodeError:
                    # If not JSON, structure the response
                    analysis_result = {
                        "analysis": {
                            "raw_response": response_text,
                            "note": "Analysis based on AI interpretation"
                        },
                        "plan": {
                            "description": "Video generation plan based on analysis",
                            "recommended_model": "runwayml_gen4",
                            "scenes": ["Scene 1: Opening", "Scene 2: Main content", "Scene 3: Conclusion"]
                        }
                    }
            finally:
                loop.close()
            
        except Exception as e:
            # Fallback analysis if AI service fails
            analysis_result = {
                "analysis": {
                    "note": f"Fallback analysis - AI service error: {str(e)}",
                    "file_path": sample_video_path,
                    "status": "analyzed_with_fallback"
                },
                "plan": {
                    "description": "Basic video generation plan",
                    "recommended_model": "runwayml_gen4",
                    "scenes": ["Scene 1: Video content recreation"],
                    "note": "Using fallback plan due to AI service issues"
                }
            }
        
        # Update project with analysis results
        db.video_projects.update_one(
            {"id": project_id},
            {"$set": {
                "video_analysis": analysis_result.get("analysis"),
                "generation_plan": analysis_result.get("plan"),
                "status": "planning",
                "progress": 50.0,
                "updated_at": datetime.utcnow()
            }}
        )
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                "message": "Video analysis completed successfully",
                "analysis": analysis_result.get("analysis"),
                "plan": analysis_result.get("plan"),
                "project_id": project_id
            })
        }
        
    except Exception as e:
        # Update project status to failed
        try:
            project_id = query.get('project_id') or body.get('project_id')
            if project_id:
                db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {
                        "status": "failed",
                        "error_message": str(e),
                        "updated_at": datetime.utcnow()
                    }}
                )
        except:
            pass
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }