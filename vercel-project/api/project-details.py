"""Project details API endpoint for Vercel with PostgreSQL"""
import json
import sys
import os

def handler(request):
    """Handle project details request"""
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
        
        from database import ProjectOperations, ChatOperations
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
        
        # Get chat history
        chat_history = ChatOperations.get_chat_history(project_id, 20)
        
        # Convert UUID and datetime objects to string/ISO format for JSON serialization
        project_data = dict(project)
        project_data['id'] = str(project_data['id'])
        
        if project_data.get('created_at'):
            project_data['created_at'] = project_data['created_at'].isoformat()
        if project_data.get('updated_at'):
            project_data['updated_at'] = project_data['updated_at'].isoformat()
        if project_data.get('generation_started_at'):
            project_data['generation_started_at'] = project_data['generation_started_at'].isoformat()
        if project_data.get('generation_completed_at'):
            project_data['generation_completed_at'] = project_data['generation_completed_at'].isoformat()
        
        # Convert Decimal to float for JSON serialization
        if project_data.get('progress'):
            project_data['progress'] = float(project_data['progress'])
        
        # Format chat history
        formatted_chat = []
        for chat in chat_history:
            formatted_chat.append({
                "id": str(chat['id']),
                "message": chat['message'],
                "response": chat['response'],
                "created_at": chat['created_at'].isoformat() if chat.get('created_at') else None
            })
        
        project_data['chat_history'] = formatted_chat
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(project_data)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }