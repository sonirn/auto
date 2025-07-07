"""
Vercel entry point for FastAPI application - Minimal Version
"""
from server_minimal import app

# This is what Vercel will use as the ASGI application
# The app instance is imported from server_minimal.py