#!/usr/bin/env python3
import os
import sys
import uuid
import requests
import json
from datetime import datetime

# API URL
BACKEND_URL = "https://cf243ac4-bbe4-47e1-890a-76bc95d374a8.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def test_database_status():
    """Test the database status endpoint"""
    url = f"{API_URL}/database/status"
    response = requests.get(url)
    print(f"Database status: {response.json()}")
    return response.json().get('available', False)

def test_storage_status():
    """Test the storage status endpoint"""
    url = f"{API_URL}/storage/status"
    response = requests.get(url)
    print(f"Storage status: {response.json()}")
    return response.json().get('available', False)

def test_project_creation():
    """Test project creation with the default user ID"""
    url = f"{API_URL}/projects"
    payload = {"user_id": "00000000-0000-0000-0000-000000000001"}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"Created project with ID: {data['id']}")
            print(f"Project user_id: {data['user_id']}")
            return data['id']
        else:
            print(f"Project creation failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error creating project: {str(e)}")
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
    files = {'file': ('sample.mp4', open(sample_video_path, 'rb'), 'video/mp4')}
    
    try:
        response = requests.post(video_url, files=files)
        print(f"Video upload response: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error uploading video: {str(e)}")
    
    # Test image upload
    image_url = f"{API_URL}/projects/{project_id}/upload-character"
    files = {'file': ('sample.jpg', open(sample_image_path, 'rb'), 'image/jpeg')}
    
    try:
        response = requests.post(image_url, files=files)
        print(f"Image upload response: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error uploading image: {str(e)}")
    
    # Test audio upload
    audio_url = f"{API_URL}/projects/{project_id}/upload-audio"
    files = {'file': ('sample.mp3', open(sample_audio_path, 'rb'), 'audio/mpeg')}
    
    try:
        response = requests.post(audio_url, files=files)
        print(f"Audio upload response: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error uploading audio: {str(e)}")
    
    return True

def test_video_analysis(project_id):
    """Test video analysis for a project"""
    if not project_id:
        print("No project ID available, skipping video analysis")
        return False
    
    url = f"{API_URL}/projects/{project_id}/analyze"
    
    try:
        response = requests.post(url)
        print(f"Video analysis response: {response.status_code}")
        print(f"Response: {response.text}")
        return True
    except Exception as e:
        print(f"Error analyzing video: {str(e)}")
        return False

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
    
    try:
        response = requests.post(url, json=payload)
        print(f"Chat interface response: {response.status_code}")
        print(f"Response: {response.text}")
        return True
    except Exception as e:
        print(f"Error in chat interface: {str(e)}")
        return False

def test_video_generation(project_id):
    """Test video generation for a project"""
    if not project_id:
        print("No project ID available, skipping video generation")
        return False
    
    url = f"{API_URL}/projects/{project_id}/generate"
    params = {"model": "runwayml_gen4"}
    
    try:
        response = requests.post(url, params=params)
        print(f"Video generation response: {response.status_code}")
        print(f"Response: {response.text}")
        return True
    except Exception as e:
        print(f"Error generating video: {str(e)}")
        return False

def test_project_status(project_id):
    """Test project status for a project"""
    if not project_id:
        print("No project ID available, skipping project status")
        return False
    
    url = f"{API_URL}/projects/{project_id}/status"
    
    try:
        response = requests.get(url)
        print(f"Project status response: {response.status_code}")
        print(f"Response: {response.text}")
        return True
    except Exception as e:
        print(f"Error getting project status: {str(e)}")
        return False

def test_project_details(project_id):
    """Test project details for a project"""
    if not project_id:
        print("No project ID available, skipping project details")
        return False
    
    url = f"{API_URL}/projects/{project_id}"
    
    try:
        response = requests.get(url)
        print(f"Project details response: {response.status_code}")
        print(f"Response: {response.text}")
        return True
    except Exception as e:
        print(f"Error getting project details: {str(e)}")
        return False

def test_video_download(project_id):
    """Test video download for a project"""
    if not project_id:
        print("No project ID available, skipping video download")
        return False
    
    url = f"{API_URL}/projects/{project_id}/download"
    
    try:
        response = requests.get(url)
        print(f"Video download response: {response.status_code}")
        print(f"Response: {response.text[:200]}...")  # Truncate long responses
        return True
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return False

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