"""Projects API endpoints for Vercel with PostgreSQL"""
import json
import uuid
from datetime import datetime
from typing import Optional

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
        
        # Import here to avoid top-level imports
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
        
        from database import ProjectOperations, PROJECT_STATUS
        from auth import auth_service
        
        # Get authorization header
        auth_header = headers.get('authorization') or headers.get('Authorization')
        user_id = auth_service.get_current_user(auth_header)
        
        if not user_id:
            return {
                'statusCode': 401,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Authentication required'})
            }
        
        if method == 'GET':
            # List projects
            projects = ProjectOperations.get_projects_by_user(user_id)
            
            # Convert UUID and datetime to string for JSON serialization
            for project in projects:
                project['id'] = str(project['id'])
                if project.get('created_at'):
                    project['created_at'] = project['created_at'].isoformat()
                if project.get('updated_at'):
                    project['updated_at'] = project['updated_at'].isoformat()
            
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({"projects": projects})
            }
        
        elif method == 'POST':
            # Create project
            project_id = str(uuid.uuid4())
            project_data = {
                "id": project_id,
                "user_id": user_id,
                "status": PROJECT_STATUS["UPLOADING"],
                "created_at": datetime.utcnow().isoformat(),
                "progress": 0.0,
                "estimated_time_remaining": 0,
                "download_count": 0
            }
            
            # Save to database
            created_project = ProjectOperations.create_project(project_data)
            
            if created_project:
                # Convert UUID and datetime to string for JSON serialization
                created_project['id'] = str(created_project['id'])
                if created_project.get('created_at'):
                    created_project['created_at'] = created_project['created_at'].isoformat()
                if created_project.get('updated_at'):
                    created_project['updated_at'] = created_project['updated_at'].isoformat()
                
                return {
                    'statusCode': 201,
                    'headers': cors_headers,
                    'body': json.dumps(created_project)
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': cors_headers,
                    'body': json.dumps({'error': 'Failed to create project'})
                }
        
        elif method == 'DELETE':
            # Delete project - get project ID from query
            project_id = query.get('project_id')
            if not project_id:
                return {
                    'statusCode': 400,
                    'headers': cors_headers,
                    'body': json.dumps({'error': 'Project ID required'})
                }
            
            success = ProjectOperations.delete_project(project_id, user_id)
            
            if not success:
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