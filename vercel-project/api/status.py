"""Project status API endpoint for Vercel with PostgreSQL"""
import json
import sys
import os

def handler(request):
    """Handle project status request"""
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
        
        # Convert datetime objects to ISO format for JSON serialization
        created_at = project.get('created_at')
        updated_at = project.get('updated_at')
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                "project_id": project_id,
                "status": project.get('status', 'unknown'),
                "progress": float(project.get('progress', 0.0)),
                "estimated_time_remaining": project.get('estimated_time_remaining', 0),
                "created_at": created_at.isoformat() if created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None,
                "error_message": project.get('error_message'),
                "ai_model": project.get('ai_model')
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }