"""Projects API endpoint for Vercel deployment"""
import json
import uuid
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def handler(request):
    """Handle HTTP requests for projects"""
    try:
        method = request.get('method', 'GET')
        headers = request.get('headers', {})
        query = request.get('query', {})
        body = request.get('body', {})
        
        # Handle CORS
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Content-Type': 'application/json'
        }
        
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        # Import database and auth
        from database import db
        
        # Get user ID (simplified auth for now)
        user_id = "default_user"
        auth_header = headers.get('authorization') or headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # In production, validate JWT token here
            user_id = "authenticated_user"
        
        if method == 'GET':
            # List projects
            projects = db.video_projects.find({"user_id": user_id})
            project_list = []
            
            # Convert to list (sync operation for Vercel)
            if hasattr(projects, 'items'):
                project_list = projects.items
            else:
                # Handle different database implementations
                project_list = []
            
            # Convert UUIDs to strings for JSON serialization
            for project in project_list:
                if project.get('id'):
                    project['id'] = str(project['id'])
                if project.get('user_id'):
                    project['user_id'] = str(project['user_id'])
                if project.get('created_at'):
                    project['created_at'] = project['created_at'].isoformat() if hasattr(project['created_at'], 'isoformat') else str(project['created_at'])
            
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({"projects": project_list})
            }
        
        elif method == 'POST':
            # Create project
            project_id = str(uuid.uuid4())
            project_data = {
                "id": project_id,
                "user_id": user_id,
                "status": "uploading",
                "created_at": datetime.utcnow(),
                "progress": 0.0,
                "estimated_time_remaining": 0,
                "download_count": 0
            }
            
            # Save to database
            db.video_projects.insert_one(project_data)
            
            # Prepare response
            response_data = dict(project_data)
            response_data['id'] = str(response_data['id'])
            response_data['created_at'] = response_data['created_at'].isoformat()
            
            return {
                'statusCode': 201,
                'headers': cors_headers,
                'body': json.dumps(response_data)
            }
        
        elif method == 'DELETE':
            # Delete project
            project_id = query.get('project_id')
            if not project_id:
                return {
                    'statusCode': 400,
                    'headers': cors_headers,
                    'body': json.dumps({'error': 'Project ID required'})
                }
            
            result = db.video_projects.delete_one({"id": project_id, "user_id": user_id})
            
            if hasattr(result, 'deleted_count') and result.deleted_count == 0:
                return {
                    'statusCode': 404,
                    'headers': cors_headers,
                    'body': json.dumps({'error': 'Project not found'})
                }
            
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({"message": "Project deleted successfully"})
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }