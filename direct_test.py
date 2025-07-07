#!/usr/bin/env python3
import os
import sys
import uuid
import subprocess
import json
from datetime import datetime

# API URL
BACKEND_URL = "https://e7f16282-da39-498b-9a0d-26fbf5bf2dc4.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def curl_get(url):
    """Execute a curl GET request"""
    cmd = ["curl", "-s", url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Curl command failed: {result.stderr}")
        return None
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON response: {result.stdout}")
        return {"raw_response": result.stdout}

def curl_post(url, json_data=None, params=None):
    """Execute a curl POST request with JSON data"""
    cmd = ["curl", "-s", "-X", "POST"]
    
    # Add headers
    cmd.extend(["-H", "Content-Type: application/json"])
    
    # Add JSON data
    if json_data:
        cmd.extend(["-d", json.dumps(json_data)])
    
    # Add query parameters
    if params:
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{url}?{param_str}"
    
    # Add URL
    cmd.append(url)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Curl command failed: {result.stderr}")
        return None
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON response: {result.stdout}")
        return {"raw_response": result.stdout}

def curl_upload_file(url, file_path, file_type):
    """Execute a curl POST request with file upload"""
    cmd = [
        "curl", "-s", "-X", "POST", 
        url,
        "-F", f"file=@{file_path};type={file_type}"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Curl command failed: {result.stderr}")
        return None
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON response: {result.stdout}")
        return {"raw_response": result.stdout}

def test_database_status():
    """Test the database status endpoint"""
    url = f"{API_URL}/database/status"
    response = curl_get(url)
    print(f"Database status: {response}")
    return response.get('available', False)

def test_storage_status():
    """Test the storage status endpoint"""
    url = f"{API_URL}/storage/status"
    response = curl_get(url)
    print(f"Storage status: {response}")
    return response.get('available', False)

def test_project_creation():
    """Test project creation with the default user ID"""
    url = f"{API_URL}/projects"
    payload = {"user_id": "00000000-0000-0000-0000-000000000001"}
    
    response = curl_post(url, payload)
    
    if response and 'id' in response:
        print(f"Created project with ID: {response['id']}")
        print(f"Project user_id: {response['user_id']}")
        return response['id']
    else:
        print(f"Project creation failed: {response}")
        return None

def test_file_uploads(project_id):
    """Test file uploads for a project"""
    if not project_id:
        print("No project ID available, skipping file uploads")
        return False
    
    # Create sample files
    sample_video_path = "/tmp/sample_video.mp4"
    sample_image_path = "/tmp/sample_image.jpg"
    sample_audio_path = "/tmp/sample_audio.mp3"
    
    with open(sample_video_path, 'wb') as f:
        f.write(b'DUMMY VIDEO CONTENT')
    
    with open(sample_image_path, 'wb') as f:
        f.write(b'DUMMY IMAGE CONTENT')
    
    with open(sample_audio_path, 'wb') as f:
        f.write(b'DUMMY AUDIO CONTENT')
    
    # Test video upload
    video_url = f"{API_URL}/projects/{project_id}/upload-sample"
    video_response = curl_upload_file(video_url, sample_video_path, 'video/mp4')
    print(f"Video upload response: {video_response}")
    
    # Test image upload
    image_url = f"{API_URL}/projects/{project_id}/upload-character"
    image_response = curl_upload_file(image_url, sample_image_path, 'image/jpeg')
    print(f"Image upload response: {image_response}")
    
    # Test audio upload
    audio_url = f"{API_URL}/projects/{project_id}/upload-audio"
    audio_response = curl_upload_file(audio_url, sample_audio_path, 'audio/mpeg')
    print(f"Audio upload response: {audio_response}")
    
    return True

def test_video_analysis(project_id):
    """Test video analysis for a project"""
    if not project_id:
        print("No project ID available, skipping video analysis")
        return False
    
    url = f"{API_URL}/projects/{project_id}/analyze"
    response = curl_post(url)
    print(f"Video analysis response: {response}")
    return True

def test_chat_interface(project_id):
    """Test chat interface for a project"""
    if not project_id:
        print("No project ID available, skipping chat interface")
        return False
    
    url = f"{API_URL}/projects/{project_id}/chat"
    payload = {
        "project_id": project_id,
        "message": "Can you make the video more vibrant and colorful with faster pacing?",
        "user_id": "00000000-0000-0000-0000-000000000001"
    }
    
    response = curl_post(url, payload)
    print(f"Chat interface response: {response}")
    return True

def test_video_generation(project_id):
    """Test video generation for a project"""
    if not project_id:
        print("No project ID available, skipping video generation")
        return False
    
    url = f"{API_URL}/projects/{project_id}/generate"
    params = {"model": "runwayml_gen4"}
    
    response = curl_post(url, params=params)
    print(f"Video generation response: {response}")
    return True

def test_project_status(project_id):
    """Test project status for a project"""
    if not project_id:
        print("No project ID available, skipping project status")
        return False
    
    url = f"{API_URL}/projects/{project_id}/status"
    response = curl_get(url)
    print(f"Project status response: {response}")
    return True

def test_project_details(project_id):
    """Test project details for a project"""
    if not project_id:
        print("No project ID available, skipping project details")
        return False
    
    url = f"{API_URL}/projects/{project_id}"
    response = curl_get(url)
    print(f"Project details response: {response}")
    return True

def test_video_download(project_id):
    """Test video download for a project"""
    if not project_id:
        print("No project ID available, skipping video download")
        return False
    
    url = f"{API_URL}/projects/{project_id}/download"
    response = curl_get(url)
    print(f"Video download response: {response}")
    return True

def run_all_tests():
    """Run all tests"""
    print("\n=== Testing Database Status ===")
    db_available = test_database_status()
    
    print("\n=== Testing Storage Status ===")
    storage_available = test_storage_status()
    
    print("\n=== Testing Project Creation ===")
    project_id = test_project_creation()
    
    if project_id:
        print("\n=== Testing File Uploads ===")
        test_file_uploads(project_id)
        
        print("\n=== Testing Video Analysis ===")
        test_video_analysis(project_id)
        
        print("\n=== Testing Chat Interface ===")
        test_chat_interface(project_id)
        
        print("\n=== Testing Video Generation ===")
        test_video_generation(project_id)
        
        print("\n=== Testing Project Status ===")
        test_project_status(project_id)
        
        print("\n=== Testing Project Details ===")
        test_project_details(project_id)
        
        print("\n=== Testing Video Download ===")
        test_video_download(project_id)
    
    print("\n=== Test Summary ===")
    print(f"Database available: {db_available}")
    print(f"Storage available: {storage_available}")
    print(f"Project created: {project_id is not None}")

if __name__ == "__main__":
    run_all_tests()