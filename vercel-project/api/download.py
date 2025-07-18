"""Video download API endpoint for Vercel with PostgreSQL"""
import json
import sys
import os
import base64

def handler(request):
    """Handle video download request"""
    try:
        method = request.get('method', 'GET')
        headers = request.get('headers', {})
        query = request.get('query', {})
        
        # Handle CORS
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Content-Type': 'application/json'
        }
        
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        if method != 'GET':
            return {
                'statusCode': 405,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        # Import here to avoid top-level imports
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
        
        from database import ProjectOperations
        from auth import auth_service
        from cloud_storage import cloud_storage_service
        
        # Get authorization header
        auth_header = headers.get('authorization') or headers.get('Authorization')
        user_id = auth_service.get_current_user(auth_header)
        
        if not user_id:
            return {
                'statusCode': 401,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Authentication required'})
            }
        
        # Get project ID from query
        project_id = query.get('project_id')
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
        
        # Check if video is ready
        if project.get('status') != 'completed':
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Video not ready for download'})
            }
        
        # Get video path
        video_path = project.get('generated_video_path')
        if not video_path:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'No generated video available'})
            }
        
        # Download video from cloud storage
        video_content = cloud_storage_service.download_file_sync(video_path)
        
        # Convert to base64 for JSON response
        video_base64 = base64.b64encode(video_content).decode()
        
        # Update download count
        ProjectOperations.update_project(project_id, {
            "download_count": project.get('download_count', 0) + 1
        })
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                "video_base64": video_base64,
                "filename": f"generated_video_{project_id}.mp4",
                "content_type": "video/mp4",
                "project_id": project_id
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }