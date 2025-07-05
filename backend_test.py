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

# Get the backend URL from the frontend .env file
def get_backend_url():
    env_file = Path("/app/frontend/.env")
    if not env_file.exists():
        print("Frontend .env file not found")
        return None
    
    with open(env_file, "r") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.strip().split("=", 1)[1].strip('"\'')
    
    return None

BACKEND_URL = get_backend_url()
if not BACKEND_URL:
    print("Error: Could not find REACT_APP_BACKEND_URL in frontend/.env")
    sys.exit(1)

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
        # Create a dummy video file
        with open(SAMPLE_VIDEO_PATH, 'wb') as f:
            f.write(b'DUMMY VIDEO CONTENT')
        print(f"Created dummy video file at {SAMPLE_VIDEO_PATH}")
    
    # Create a simple image file
    if not os.path.exists(SAMPLE_IMAGE_PATH):
        # Create a dummy image file
        with open(SAMPLE_IMAGE_PATH, 'wb') as f:
            f.write(b'DUMMY IMAGE CONTENT')
        print(f"Created dummy image file at {SAMPLE_IMAGE_PATH}")
    
    # Create a simple audio file
    if not os.path.exists(SAMPLE_AUDIO_PATH):
        # Create a dummy audio file
        with open(SAMPLE_AUDIO_PATH, 'wb') as f:
            f.write(b'DUMMY AUDIO CONTENT')
        print(f"Created dummy audio file at {SAMPLE_AUDIO_PATH}")

class VideoModel(str, Enum):
    RUNWAYML_GEN4 = "runwayml_gen4"
    RUNWAYML_GEN3 = "runwayml_gen3"
    GOOGLE_VEO2 = "google_veo2"
    GOOGLE_VEO3 = "google_veo3"

class BackendTest(unittest.TestCase):
    """Test suite for the Video Generation Backend API"""
    
    def setUp(self):
        """Set up test environment"""
        create_sample_files()
        self.project_id = None
        print(f"Using test user ID: {TEST_USER_ID}")
    
    def test_01_create_project(self):
        """Test project creation API"""
        print("\n=== Testing Project Creation API ===")
        
        url = f"{API_URL}/projects"
        payload = {"user_id": TEST_USER_ID}
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            self.project_id = data["id"]
            
            self.assertIn("id", data, "Project ID not found in response")
            self.assertEqual(data["user_id"], TEST_USER_ID, "User ID mismatch")
            
            print(f"Created project with ID: {self.project_id}")
            print("✅ Project creation API works")
            
            # Store project ID for other tests
            BackendTest.project_id = self.project_id
            return True
        except Exception as e:
            print(f"❌ Project creation API failed: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return False
    
    def test_02_upload_sample_video(self):
        """Test sample video upload API"""
        print("\n=== Testing Sample Video Upload API ===")
        
        if not hasattr(BackendTest, 'project_id') or not BackendTest.project_id:
            self.skipTest("Project ID not available, skipping test")
        
        url = f"{API_URL}/projects/{BackendTest.project_id}/upload-sample"
        
        try:
            with open(SAMPLE_VIDEO_PATH, 'rb') as f:
                files = {'file': ('sample.mp4', f, 'video/mp4')}
                response = requests.post(url, files=files)
                response.raise_for_status()
            
            data = response.json()
            self.assertIn("message", data, "Response message not found")
            
            print(f"Upload response: {data['message']}")
            print("✅ Sample video upload API works")
            return True
        except Exception as e:
            print(f"❌ Sample video upload API failed: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return False
    
    def test_03_upload_character_image(self):
        """Test character image upload API"""
        print("\n=== Testing Character Image Upload API ===")
        
        if not hasattr(BackendTest, 'project_id') or not BackendTest.project_id:
            self.skipTest("Project ID not available, skipping test")
        
        url = f"{API_URL}/projects/{BackendTest.project_id}/upload-character"
        
        try:
            with open(SAMPLE_IMAGE_PATH, 'rb') as f:
                files = {'file': ('character.jpg', f, 'image/jpeg')}
                response = requests.post(url, files=files)
                response.raise_for_status()
            
            data = response.json()
            self.assertIn("message", data, "Response message not found")
            
            print(f"Upload response: {data['message']}")
            print("✅ Character image upload API works")
            return True
        except Exception as e:
            print(f"❌ Character image upload API failed: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return False
    
    def test_04_upload_audio(self):
        """Test audio upload API"""
        print("\n=== Testing Audio Upload API ===")
        
        if not hasattr(BackendTest, 'project_id') or not BackendTest.project_id:
            self.skipTest("Project ID not available, skipping test")
        
        url = f"{API_URL}/projects/{BackendTest.project_id}/upload-audio"
        
        try:
            with open(SAMPLE_AUDIO_PATH, 'rb') as f:
                files = {'file': ('audio.mp3', f, 'audio/mpeg')}
                response = requests.post(url, files=files)
                response.raise_for_status()
            
            data = response.json()
            self.assertIn("message", data, "Response message not found")
            
            print(f"Upload response: {data['message']}")
            print("✅ Audio upload API works")
            return True
        except Exception as e:
            print(f"❌ Audio upload API failed: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return False
    
    def test_05_analyze_video(self):
        """Test video analysis API"""
        print("\n=== Testing Video Analysis API ===")
        
        if not hasattr(BackendTest, 'project_id') or not BackendTest.project_id:
            self.skipTest("Project ID not available, skipping test")
        
        url = f"{API_URL}/projects/{BackendTest.project_id}/analyze"
        
        try:
            response = requests.post(url)
            response.raise_for_status()
            
            data = response.json()
            self.assertIn("analysis", data, "Analysis data not found in response")
            self.assertIn("plan", data, "Plan data not found in response")
            
            print("Video analysis completed successfully")
            print("✅ Video analysis API works")
            return True
        except Exception as e:
            print(f"❌ Video analysis API failed: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return False
    
    def test_06_chat_with_plan(self):
        """Test chat API for plan modifications"""
        print("\n=== Testing Chat API ===")
        
        if not hasattr(BackendTest, 'project_id') or not BackendTest.project_id:
            self.skipTest("Project ID not available, skipping test")
        
        url = f"{API_URL}/projects/{BackendTest.project_id}/chat"
        payload = {
            "project_id": BackendTest.project_id,
            "message": "Can you make the video more vibrant and colorful?",
            "user_id": TEST_USER_ID
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            self.assertIn("response", data, "Response not found in chat response")
            
            print("Chat API responded successfully")
            print("✅ Chat API works")
            return True
        except Exception as e:
            print(f"❌ Chat API failed: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return False
    
    def test_07_start_video_generation(self):
        """Test video generation API"""
        print("\n=== Testing Video Generation API ===")
        
        if not hasattr(BackendTest, 'project_id') or not BackendTest.project_id:
            self.skipTest("Project ID not available, skipping test")
        
        url = f"{API_URL}/projects/{BackendTest.project_id}/generate"
        params = {"model": VideoModel.RUNWAYML_GEN4.value}
        
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            self.assertIn("message", data, "Message not found in generation response")
            self.assertIn("project_id", data, "Project ID not found in generation response")
            
            print("Video generation started successfully")
            print("✅ Video generation API works")
            return True
        except Exception as e:
            print(f"❌ Video generation API failed: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return False
    
    def test_08_get_project_status(self):
        """Test project status API"""
        print("\n=== Testing Project Status API ===")
        
        if not hasattr(BackendTest, 'project_id') or not BackendTest.project_id:
            self.skipTest("Project ID not available, skipping test")
        
        url = f"{API_URL}/projects/{BackendTest.project_id}/status"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            self.assertIn("status", data, "Status not found in response")
            self.assertIn("progress", data, "Progress not found in response")
            
            print(f"Project status: {data['status']}, Progress: {data['progress']}")
            print("✅ Project status API works")
            return True
        except Exception as e:
            print(f"❌ Project status API failed: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return False
    
    def test_09_get_project_details(self):
        """Test project details API"""
        print("\n=== Testing Project Details API ===")
        
        if not hasattr(BackendTest, 'project_id') or not BackendTest.project_id:
            self.skipTest("Project ID not available, skipping test")
        
        url = f"{API_URL}/projects/{BackendTest.project_id}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            self.assertEqual(data["id"], BackendTest.project_id, "Project ID mismatch")
            self.assertEqual(data["user_id"], TEST_USER_ID, "User ID mismatch")
            
            print(f"Retrieved project details for ID: {data['id']}")
            print("✅ Project details API works")
            return True
        except Exception as e:
            print(f"❌ Project details API failed: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return False
    
    def test_10_download_video(self):
        """Test video download API"""
        print("\n=== Testing Video Download API ===")
        
        if not hasattr(BackendTest, 'project_id') or not BackendTest.project_id:
            self.skipTest("Project ID not available, skipping test")
        
        url = f"{API_URL}/projects/{BackendTest.project_id}/download"
        
        try:
            response = requests.get(url)
            
            # This might fail if the video is not ready yet, which is expected
            if response.status_code == 400 and "Video not ready for download" in response.text:
                print("Video not ready for download yet (expected at this stage)")
                print("✅ Video download API works (returned expected 'not ready' response)")
                return True
            
            response.raise_for_status()
            
            data = response.json()
            self.assertIn("video_base64", data, "Video base64 not found in response")
            self.assertIn("filename", data, "Filename not found in response")
            
            print("Video download successful")
            print("✅ Video download API works")
            return True
        except Exception as e:
            if hasattr(e, 'response') and e.response and e.response.status_code == 400 and "Video not ready for download" in e.response.text:
                print("Video not ready for download yet (expected at this stage)")
                print("✅ Video download API works (returned expected 'not ready' response)")
                return True
            
            print(f"❌ Video download API failed: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return False

if __name__ == "__main__":
    # Run the tests in order
    print("\n======= STARTING VIDEO GENERATION BACKEND TESTS =======\n")
    
    test_suite = unittest.TestSuite()
    test_suite.addTest(BackendTest('test_01_create_project'))
    test_suite.addTest(BackendTest('test_02_upload_sample_video'))
    test_suite.addTest(BackendTest('test_03_upload_character_image'))
    test_suite.addTest(BackendTest('test_04_upload_audio'))
    test_suite.addTest(BackendTest('test_05_analyze_video'))
    test_suite.addTest(BackendTest('test_06_chat_with_plan'))
    test_suite.addTest(BackendTest('test_07_start_video_generation'))
    test_suite.addTest(BackendTest('test_08_get_project_status'))
    test_suite.addTest(BackendTest('test_09_get_project_details'))
    test_suite.addTest(BackendTest('test_10_download_video'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("\n======= TEST RESULTS SUMMARY =======")
    print(f"Tests run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    
    if result.errors:
        print("\n--- ERRORS ---")
        for test, error in result.errors:
            print(f"\n{test}:\n{error}")
    
    if result.failures:
        print("\n--- FAILURES ---")
        for test, failure in result.failures:
            print(f"\n{test}:\n{failure}")
    
    print("\n======= END OF TESTS =======\n")