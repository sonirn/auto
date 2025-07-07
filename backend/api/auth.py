"""Authentication endpoints for Vercel deployment"""
from fastapi import HTTPException
import httpx
import os
import json
from datetime import datetime
from database import db

async def register(request):
    """Register a new user with Supabase"""
    try:
        body = request.get('body', {})
        email = body.get('email')
        password = body.get('password')
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Email and password are required'})
            }
        
        # Register with Supabase
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{os.environ['SUPABASE_URL']}/auth/v1/signup",
                headers={
                    "apikey": os.environ['SUPABASE_KEY'],
                    "Content-Type": "application/json"
                },
                json={
                    "email": email,
                    "password": password
                }
            )
            
            if response.status_code != 200:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': f'Registration failed: {response.text}'})
                }
            
            data = response.json()
            
            # Create user record in our database
            user_data = {
                "id": data["user"]["id"],
                "email": email,
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "projects": [],
                "subscription_status": "free"
            }
            
            await db.users.insert_one(user_data)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "message": "User registered successfully",
                    "user": {
                        "id": data["user"]["id"],
                        "email": email
                    },
                    "access_token": data["access_token"]
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

async def login(request):
    """Login user with Supabase"""
    try:
        body = request.get('body', {})
        email = body.get('email')
        password = body.get('password')
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Email and password are required'})
            }
        
        # Login with Supabase
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{os.environ['SUPABASE_URL']}/auth/v1/token?grant_type=password",
                headers={
                    "apikey": os.environ['SUPABASE_KEY'],
                    "Content-Type": "application/json"
                },
                json={
                    "email": email,
                    "password": password
                }
            )
            
            if response.status_code != 200:
                return {
                    'statusCode': 401,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': f'Login failed: {response.text}'})
                }
            
            data = response.json()
            
            # Update last login in our database
            await db.users.update_one(
                {"id": data["user"]["id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "message": "Login successful",
                    "user": {
                        "id": data["user"]["id"],
                        "email": data["user"]["email"]
                    },
                    "access_token": data["access_token"]
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def handler(request):
    """Main handler for auth endpoints"""
    try:
        method = request.get('method', 'GET')
        path = request.get('path', '')
        
        # Handle CORS
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Content-Type': 'application/json'
        }
        
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        # Route to appropriate function
        if '/register' in path:
            return register(request)
        elif '/login' in path:
            return login(request)
        else:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }