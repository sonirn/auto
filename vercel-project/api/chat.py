"""Chat API endpoint for Vercel with PostgreSQL"""
import json
import sys
import os
from datetime import datetime

def handler(request):
    """Handle chat request"""
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
        
        # Get project ID and message from query or body
        project_id = query.get('project_id') or body.get('project_id')
        message = body.get('message', '')
        
        if not project_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Project ID required'})
            }
        
        if not message:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Message is required'})
            }
        
        # Get project from database
        project = ProjectOperations.get_project(project_id, user_id)
        
        if not project:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Project not found'})
            }
        
        # Get current generation plan
        generation_plan = project.get('generation_plan', {})
        
        # Create chat context
        context = f"""
        You are an AI assistant helping to modify video generation plans.
        
        Current generation plan:
        {json.dumps(generation_plan, indent=2)}
        
        User message: {message}
        
        Please provide a helpful response about modifying the generation plan.
        If the user wants to change something specific, provide updated plan suggestions.
        Keep your response concise and focused on video generation.
        """
        
        # Call Groq LLM
        groq_api_key = os.environ.get('GROQ_API_KEY')
        if not groq_api_key:
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': 'AI service not configured'})
            }
        
        import litellm
        os.environ['GROQ_API_KEY'] = groq_api_key
        
        # Use synchronous completion for Vercel
        response = litellm.completion(
            model="groq/llama3-8b-8192",
            messages=[{"role": "user", "content": context}],
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        # Save chat message to database
        ChatOperations.save_chat_message(project_id, user_id, message, ai_response)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                "message": ai_response,
                "project_id": project_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }