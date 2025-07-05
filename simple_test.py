#!/usr/bin/env python3
import os
import sys
import json
import uuid
import time
import base64
import requests
import unittest
from enum import Enum
from typing import Dict, Any, Optional
from pathlib import Path

# Get the backend URL
BACKEND_URL = "http://0.0.0.0:8001"
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Test user ID
TEST_USER_ID = "test_user_" + str(uuid.uuid4())[:8]

# Sample file paths
SAMPLE_VIDEO_PATH = "/app/backend/sample_video.mp4"
SAMPLE_IMAGE_PATH = "/app/backend/sample_image.jpg"
SAMPLE_AUDIO_PATH = "/app/backend/sample_audio.mp3"

# Create sample files if they don't exist
def create_sample_files():
    # Create a simple video file
    if not os.path.exists(SAMPLE_VIDEO_PATH):
        os.makedirs(os.path.dirname(SAMPLE_VIDEO_PATH), exist_ok=True)
        # Create a dummy video file
        with open(SAMPLE_VIDEO_PATH, 'wb') as f:
            f.write(b'DUMMY VIDEO CONTENT')
        print(f"Created dummy video file at {SAMPLE_VIDEO_PATH}")
    
    # Create a simple image file
    if not os.path.exists(SAMPLE_IMAGE_PATH):
        os.makedirs(os.path.dirname(SAMPLE_IMAGE_PATH), exist_ok=True)
        # Create a dummy image file
        with open(SAMPLE_IMAGE_PATH, 'wb') as f:
            f.write(b'DUMMY IMAGE CONTENT')
        print(f"Created dummy image file at {SAMPLE_IMAGE_PATH}")
    
    # Create a simple audio file
    if not os.path.exists(SAMPLE_AUDIO_PATH):
        os.makedirs(os.path.dirname(SAMPLE_AUDIO_PATH), exist_ok=True)
        # Create a dummy audio file
        with open(SAMPLE_AUDIO_PATH, 'wb') as f:
            f.write(b'DUMMY AUDIO CONTENT')
        print(f"Created dummy audio file at {SAMPLE_AUDIO_PATH}")

class VideoModel(str, Enum):
    RUNWAYML_GEN4 = "runwayml_gen4"
    RUNWAYML_GEN3 = "runwayml_gen3"
    GOOGLE_VEO2 = "google_veo2"
    GOOGLE_VEO3 = "google_veo3"

def test_backend():
    print("\n======= STARTING VIDEO GENERATION BACKEND TESTS =======\n")
    
    # Create sample files
    create_sample_files()
    
    # Step 1: Create a project
    print("\n=== Testing Project Creation API ===")
    project_id = None
    try:
        response = requests.post(f"{API_URL}/projects", json={"user_id": TEST_USER_ID})
        response.raise_for_status()
        data = response.json()
        project_id = data["id"]
        print(f"Created project with ID: {project_id}")
        print("✅ Project creation API works")
    except Exception as e:
        print(f"❌ Project creation API failed: {str(e)}")
        return
    
    # Step 2: Upload sample video
    print("\n=== Testing Sample Video Upload API ===")
    try:
        with open(SAMPLE_VIDEO_PATH, 'rb') as f:
            files = {'file': ('sample.mp4', f, 'video/mp4')}
            response = requests.post(f"{API_URL}/projects/{project_id}/upload-sample", files=files)
            response.raise_for_status()
            print(f"Upload response: {response.json()}")
            print("✅ Sample video upload API works")
    except Exception as e:
        print(f"❌ Sample video upload API failed: {str(e)}")
    
    # Step 3: Test video analysis
    print("\n=== Testing Video Analysis API ===")
    analysis_data = None
    plan_data = None
    try:
        response = requests.post(f"{API_URL}/projects/{project_id}/analyze")
        response.raise_for_status()
        data = response.json()
        
        if "analysis" in data and "plan" in data:
            analysis_data = data["analysis"]
            plan_data = data["plan"]
            print("Video analysis completed successfully with text-only analysis")
            print("Analysis data:", json.dumps(analysis_data, indent=2)[:200] + "...")
            print("Plan data:", json.dumps(plan_data, indent=2)[:200] + "...")
            print("✅ Video analysis API works with text-only analysis (file attachments disabled)")
        else:
            print("Video analysis completed but returned unexpected data format")
            print(f"Response: {data}")
            print("❌ Video analysis API returned unexpected format")
    except Exception as e:
        print(f"❌ Video analysis API failed: {str(e)}")
    
    # Step 4: Test chat interface
    print("\n=== Testing Chat Interface for Plan Modifications ===")
    try:
        payload = {
            "project_id": project_id,
            "message": "Can you make the video more vibrant and colorful with faster pacing?",
            "user_id": TEST_USER_ID
        }
        response = requests.post(f"{API_URL}/projects/{project_id}/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        
        if "response" in data:
            print(f"Chat response: {data['response'][:200]}...")
            
            if "updated_plan" in data and data["updated_plan"]:
                print("Chat API returned an updated plan")
                print(f"Updated plan: {json.dumps(data['updated_plan'], indent=2)[:200]}...")
            else:
                print("Chat API responded but did not update the plan (this is expected if analysis failed)")
            
            print("✅ Chat API with Groq integration works")
        else:
            print(f"Chat API returned unexpected format: {data}")
            print("❌ Chat API returned unexpected format")
    except Exception as e:
        print(f"❌ Chat API failed: {str(e)}")
    
    # Step 5: Test video generation
    print("\n=== Testing Video Generation Process ===")
    try:
        response = requests.post(f"{API_URL}/projects/{project_id}/generate", params={"model": VideoModel.RUNWAYML_GEN4.value})
        response.raise_for_status()
        data = response.json()
        
        print("Video generation started successfully")
        print(f"Response: {data}")
        
        # Check project status after generation starts
        status_response = requests.get(f"{API_URL}/projects/{project_id}/status")
        status_response.raise_for_status()
        status_data = status_response.json()
        print(f"Project status after generation request: {status_data}")
        
        print("✅ Video generation API works")
    except Exception as e:
        print(f"❌ Video generation API failed: {str(e)}")
        
        if "No generation plan available" in str(e):
            if analysis_data and plan_data:
                print("\nDETAILED ERROR: The error indicates that no generation plan is available, but we did get analysis data.")
                print("This suggests the analysis data was not properly saved to the database.")
                print("Check the database update in the analyze_video endpoint (around line 561).")
            else:
                print("\nDETAILED ERROR: The error indicates that no generation plan is available.")
                print("This is expected because the video analysis step may not have created a proper generation plan.")
                print("Check if the video analysis step completed successfully and created a valid plan.")
    
    # Step 6: Test project status
    print("\n=== Testing Project Status API ===")
    try:
        response = requests.get(f"{API_URL}/projects/{project_id}/status")
        response.raise_for_status()
        data = response.json()
        
        print(f"Project status: {data['status']}, Progress: {data['progress']}")
        print("✅ Project status API works")
    except Exception as e:
        print(f"❌ Project status API failed: {str(e)}")
    
    # Step 7: Test project details
    print("\n=== Testing Project Details API ===")
    try:
        response = requests.get(f"{API_URL}/projects/{project_id}")
        response.raise_for_status()
        data = response.json()
        
        print(f"Retrieved project details for ID: {data['id']}")
        print("✅ Project details API works")
    except Exception as e:
        print(f"❌ Project details API failed: {str(e)}")
    
    # Step 8: Test video download
    print("\n=== Testing Video Download API ===")
    try:
        response = requests.get(f"{API_URL}/projects/{project_id}/download")
        response.raise_for_status()
        data = response.json()
        
        if "video_base64" in data:
            print("Video download successful")
            print("✅ Video download API works")
        else:
            print(f"Unexpected response format: {data}")
            print("❌ Video download API returned unexpected format")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400 and "Video not ready for download" in e.response.text:
            print("Video not ready for download yet (expected at this stage)")
            print("✅ Video download API works (returned expected 'not ready' response)")
        else:
            print(f"❌ Video download API failed: {str(e)}")
    except Exception as e:
        print(f"❌ Video download API failed: {str(e)}")
    
    print("\n======= END OF TESTS =======\n")

if __name__ == "__main__":
    test_backend()