"""Video analysis API endpoint for Vercel"""
import json
import sys
import os
from datetime import datetime

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
        
        # Import here to avoid top-level imports
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
        
        from database import get_collection_sync, PROJECT_STATUS
        from auth import auth_service
        from video_analysis import VideoAnalysisService
        
        # Get authorization header
        auth_header = headers.get('authorization') or headers.get('Authorization')
        user_id = auth_service.get_current_user(auth_header)
        
        if not user_id:
            return {
                'statusCode': 401,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Authentication required'})
            }
        
        # Get project ID from query or body
        project_id = query.get('project_id') or body.get('project_id')
        if not project_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Project ID required'})
            }
        
        # Get project from database
        collection = get_collection_sync('video_projects')
        project = collection.find_one({"_id": project_id, "user_id": user_id})
        
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
        
        # Perform analysis (async call in sync context)
        import asyncio
        try:
            # Create new event loop for this request
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            analysis_result = loop.run_until_complete(
                analysis_service.analyze_video(
                    video_path=sample_video_path,
                    character_image_path=project.get('character_image_path'),
                    audio_path=project.get('audio_path')
                )
            )
        finally:
            loop.close()
        
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
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                "message": "Video analysis completed successfully",
                "analysis": analysis_result,
                "project_id": project_id
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }