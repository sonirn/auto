"""Character image upload API endpoint for Vercel with PostgreSQL"""
import json
import base64
import sys
import os
from datetime import datetime

def handler(request):
    """Handle character image upload"""
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
        
        # Get project ID from query or body
        project_id = query.get('project_id') or body.get('project_id')
        if not project_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Project ID required'})
            }
        
        # Get file data from body
        file_data_b64 = body.get('file_data')
        filename = body.get('filename', 'character_image.jpg')
        content_type = body.get('content_type', 'image/jpeg')
        
        if not file_data_b64:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'No file data provided'})
            }
        
        try:
            file_data = base64.b64decode(file_data_b64)
        except:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Invalid file data format'})
            }
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if content_type not in allowed_types:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Invalid file type. Only image files are allowed.'})
            }
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_data) > max_size:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'File too large. Maximum size is 10MB.'})
            }
        
        # Upload to cloud storage
        file_url = cloud_storage_service.upload_file_sync(
            content=file_data,
            user_id=user_id,
            project_id=project_id,
            folder='input',
            filename=filename,
            content_type=content_type
        )
        
        # Update project in database
        success = ProjectOperations.update_project(project_id, {
            "character_image_path": file_url
        })
        
        if not success:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Project not found'})
            }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                "message": "Character image uploaded successfully",
                "file_url": file_url,
                "project_id": project_id
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }