"""Video generation API endpoint for Vercel with PostgreSQL"""
import json
import sys
import os
from datetime import datetime

def handler(request):
    """Handle video generation request"""
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
        
        # Import here to avoid top-level imports
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
        
        from database import ProjectOperations, PROJECT_STATUS
        from auth import auth_service
        from video_generation import VideoGenerationService, VideoModel
        
        # Get authorization header
        auth_header = headers.get('authorization') or headers.get('Authorization')
        user_id = auth_service.get_current_user(auth_header)
        
        if not user_id:
            return {
                'statusCode': 401,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Authentication required'})
            }
        
        # Get project ID and model from query or body
        project_id = query.get('project_id') or body.get('project_id')
        selected_model = body.get('model', 'runwayml_gen4')
        
        if not project_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Project ID required'})
            }
        
        # Get project from database
        project = ProjectOperations.get_project(project_id, user_id)
        
        if not project:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Project not found'})
            }
        
        # Check if generation plan exists
        generation_plan = project.get('generation_plan')
        if not generation_plan:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'No generation plan available. Please analyze video first.'})
            }
        
        # Update project status
        ProjectOperations.update_project(project_id, {
            "status": PROJECT_STATUS["GENERATING"],
            "progress": 60.0,
            "ai_model": selected_model,
            "generation_started_at": datetime.utcnow().isoformat()
        })
        
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
        
        # Start generation (async call in sync context)
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            generation_result = loop.run_until_complete(
                generation_service.generate_video(
                    project_id=project_id,
                    generation_plan=generation_plan,
                    model=model_enum
                )
            )
        finally:
            loop.close()
        
        # Update project with generation info
        update_data = {
            "status": PROJECT_STATUS["PROCESSING"],
            "progress": 70.0,
            "generation_job_id": generation_result.get('generation_id'),
            "estimated_time_remaining": generation_result.get('estimated_time', 120)
        }
        
        ProjectOperations.update_project(project_id, update_data)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                "message": "Video generation started successfully",
                "generation_id": generation_result.get('generation_id'),
                "model": selected_model,
                "estimated_time": generation_result.get('estimated_time', 120),
                "project_id": project_id
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }