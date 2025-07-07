"""Sample video upload API endpoint for Vercel deployment"""
import json
import base64
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def handler(request):
    """Handle sample video upload"""
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
        
        # Import database and cloud storage
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
        
        # Get file data from body
        file_data_b64 = body.get('file_data')
        filename = body.get('filename', 'sample_video.mp4')
        content_type = body.get('content_type', 'video/mp4')
        
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
        allowed_types = ['video/mp4', 'video/mov', 'video/avi', 'video/mkv']
        if content_type not in allowed_types:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Invalid file type. Only video files are allowed.'})
            }
        
        # Validate file size (max 100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        if len(file_data) > max_size:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'File too large. Maximum size is 100MB.'})
            }
        
        # For now, simulate file upload (in production, upload to cloud storage)
        # Initialize cloud storage if available
        try:
            from cloud_storage import cloud_storage_service
            
            # Try to upload to cloud storage
            if hasattr(cloud_storage_service, 'upload_file'):
                # Async upload (simplified for Vercel)
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                file_url = loop.run_until_complete(
                    cloud_storage_service.upload_file(
                        file_data, user_id, project_id, 'input', filename, content_type
                    )
                )
                loop.close()
            else:
                # Fallback local storage
                import tempfile
                import uuid
                
                temp_dir = f"/tmp/uploads/{user_id}/{project_id}/input"
                os.makedirs(temp_dir, exist_ok=True)
                
                unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_{filename}"
                file_path = os.path.join(temp_dir, unique_filename)
                
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                
                file_url = file_path
                
        except Exception as e:
            # Fallback to local storage
            import tempfile
            import uuid
            
            temp_dir = f"/tmp/uploads/{user_id}/{project_id}/input"
            os.makedirs(temp_dir, exist_ok=True)
            
            unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_{filename}"
            file_path = os.path.join(temp_dir, unique_filename)
            
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            file_url = file_path
        
        # Update project in database
        result = db.video_projects.update_one(
            {"id": project_id, "user_id": user_id},
            {"$set": {
                "sample_video_path": file_url,
                "status": "analyzing",
                "updated_at": datetime.utcnow()
            }}
        )
        
        if hasattr(result, 'matched_count') and result.matched_count == 0:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Project not found'})
            }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                "message": "Sample video uploaded successfully",
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