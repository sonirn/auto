"""
Vercel entry point for FastAPI application
"""
from server import app

# This is what Vercel will use as the ASGI application
# The app instance is imported from server.py