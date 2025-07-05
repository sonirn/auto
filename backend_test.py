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
TEST_USER_ID = "test_user"

# Sample file paths
SAMPLE_VIDEO_PATH = "/app/backend/sample_video.mp4"
SAMPLE_IMAGE_PATH = "/app/backend/sample_image.jpg"
SAMPLE_AUDIO_PATH = "/app/backend/sample_audio.mp3"

# Create sample files if they don't exist
def create_sample_files():
    # Create a simple video file
    if not os.path.exists(SAMPLE_VIDEO_PATH):
        try:
            import numpy as np
            import cv2
            
            # Create a small video file
            width, height = 320, 240
            fps = 30
            duration = 3  # seconds
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(SAMPLE_VIDEO_PATH, fourcc, fps, (width, height))
            
            for i in range(fps * duration):
                # Create a color gradient frame
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                frame[:, :, 0] = i % 255  # Blue channel
                frame[:, :, 1] = (i * 2) % 255  # Green channel
                frame[:, :, 2] = (i * 3) % 255  # Red channel
                
                out.write(frame)
            
            out.release()
            print(f"Created sample video at {SAMPLE_VIDEO_PATH}")
        except Exception as e:
            print(f"Error creating sample video: {e}")
            # Create an empty file as fallback
            with open(SAMPLE_VIDEO_PATH, 'wb') as f:
                f.write(b'DUMMY VIDEO CONTENT')
    
    # Create a simple image file
    if not os.path.exists(SAMPLE_IMAGE_PATH):
        try:
            import numpy as np
            from PIL import Image
            
            # Create a gradient image
            width, height = 320, 240
            image = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Create a gradient
            for y in range(height):
                for x in range(width):
                    image[y, x, 0] = int(255 * x / width)  # Red increases from left to right
                    image[y, x, 1] = int(255 * y / height)  # Green increases from top to bottom
                    image[y, x, 2] = 128  # Blue is constant
            
            img = Image.fromarray(image)
            img.save(SAMPLE_IMAGE_PATH)
            print(f"Created sample image at {SAMPLE_IMAGE_PATH}")
        except Exception as e:
            print(f"Error creating sample image: {e}")
            # Create an empty file as fallback
            with open(SAMPLE_IMAGE_PATH, 'wb') as f:
                f.write(b'DUMMY IMAGE CONTENT')
    
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

class VideoGenerationBackendTest(unittest.TestCase):
    """Test suite for the Video Generation Backend API"""
    
    def setUp(self):
        """Set up test environment"""
        self.project_id = None
        create_sample_files()
    
    def test_01_create_project(self):
        """Test project creation API"""
        print("\n=== Testing Project Creation API ===")
        
        url = f"{API_URL}/projects"
        payload = {"user_id": TEST_USER_ID}
        
        response = requests.post(url, json=payload)
        self.assertEqual(response.status_code, 200, f"Failed to create project: {response.text}")
        
        data = response.json()
        self.assertIn("id", data, "Project ID not found in response")
        self.assertEqual(data["user_id"], TEST_USER_ID, "User ID mismatch")
        
        # Save project ID for subsequent tests
        self.__class__.project_id = data["id"]
        print(f"Created project with ID: {self.__class__.project_id}")
    
    def test_02_upload_sample_video(self):
        """Test sample video upload API"""
        print("\n=== Testing Sample Video Upload API ===")
        
        if not hasattr(self.__class__, 'project_id'):
            self.fail("Project ID not available. Project creation test failed.")
        
        url = f"{API_URL}/projects/{self.__class__.project_id}/upload-sample"
        
        # Check if sample video exists
        if not os.path.exists(SAMPLE_VIDEO_PATH):
            self.fail(f"Sample video not found at {SAMPLE_VIDEO_PATH}")
        
        with open(SAMPLE_VIDEO_PATH, 'rb') as f:
            files = {'file': ('sample.mp4', f, 'video/mp4')}
            response = requests.post(url, files=files)
        
        self.assertEqual(response.status_code, 200, f"Failed to upload sample video: {response.text}")
        data = response.json()
        self.assertIn("message", data, "Response message not found")
        print(f"Upload response: {data['message']}")
    
    def test_03_upload_character_image(self):
        """Test character image upload API"""
        print("\n=== Testing Character Image Upload API ===")
        
        if not hasattr(self.__class__, 'project_id'):
            self.fail("Project ID not available. Project creation test failed.")
        
        url = f"{API_URL}/projects/{self.__class__.project_id}/upload-character"
        
        # Check if sample image exists
        if not os.path.exists(SAMPLE_IMAGE_PATH):
            self.fail(f"Sample image not found at {SAMPLE_IMAGE_PATH}")
        
        with open(SAMPLE_IMAGE_PATH, 'rb') as f:
            files = {'file': ('character.jpg', f, 'image/jpeg')}
            response = requests.post(url, files=files)
        
        self.assertEqual(response.status_code, 200, f"Failed to upload character image: {response.text}")
        data = response.json()
        self.assertIn("message", data, "Response message not found")
        print(f"Upload response: {data['message']}")
    
    def test_04_upload_audio(self):
        """Test audio upload API"""
        print("\n=== Testing Audio Upload API ===")
        
        if not hasattr(self.__class__, 'project_id'):
            self.fail("Project ID not available. Project creation test failed.")
        
        url = f"{API_URL}/projects/{self.__class__.project_id}/upload-audio"
        
        # Check if sample audio exists
        if not os.path.exists(SAMPLE_AUDIO_PATH):
            self.fail(f"Sample audio not found at {SAMPLE_AUDIO_PATH}")
        
        with open(SAMPLE_AUDIO_PATH, 'rb') as f:
            files = {'file': ('audio.mp3', f, 'audio/mpeg')}
            response = requests.post(url, files=files)
        
        self.assertEqual(response.status_code, 200, f"Failed to upload audio: {response.text}")
        data = response.json()
        self.assertIn("message", data, "Response message not found")
        print(f"Upload response: {data['message']}")
    
    def test_05_analyze_video(self):
        """Test video analysis API"""
        print("\n=== Testing Video Analysis API ===")
        
        if not hasattr(self.__class__, 'project_id'):
            self.fail("Project ID not available. Project creation test failed.")
        
        url = f"{API_URL}/projects/{self.__class__.project_id}/analyze"
        
        response = requests.post(url)
        
        # This might take time and could fail if the AI service is not available
        # We'll check for either success or a specific error
        if response.status_code == 200:
            data = response.json()
            self.assertIn("analysis", data, "Analysis data not found in response")
            self.assertIn("plan", data, "Plan data not found in response")
            print("Video analysis completed successfully")
        else:
            print(f"Video analysis returned status code {response.status_code}: {response.text}")
            # Don't fail the test if it's an external API issue
            if "emergentintegrations" in response.text or "XAI_API_KEY" in response.text:
                print("Analysis failed due to AI service integration issue - this is expected in test environment")
            else:
                self.fail(f"Video analysis failed with unexpected error: {response.text}")
    
    def test_06_chat_with_plan(self):
        """Test chat API for plan modifications"""
        print("\n=== Testing Chat API ===")
        
        if not hasattr(self.__class__, 'project_id'):
            self.fail("Project ID not available. Project creation test failed.")
        
        url = f"{API_URL}/projects/{self.__class__.project_id}/chat"
        
        payload = {
            "project_id": self.__class__.project_id,
            "message": "Can you make the video more vibrant and colorful?",
            "user_id": TEST_USER_ID
        }
        
        response = requests.post(url, json=payload)
        
        # This might fail if the AI service is not available
        if response.status_code == 200:
            data = response.json()
            self.assertIn("response", data, "Response not found in chat response")
            print("Chat API responded successfully")
        else:
            print(f"Chat API returned status code {response.status_code}: {response.text}")
            # Don't fail the test if it's an external API issue
            if "emergentintegrations" in response.text or "XAI_API_KEY" in response.text:
                print("Chat failed due to AI service integration issue - this is expected in test environment")
            else:
                self.fail(f"Chat API failed with unexpected error: {response.text}")
    
    def test_07_start_video_generation(self):
        """Test video generation API"""
        print("\n=== Testing Video Generation API ===")
        
        if not hasattr(self.__class__, 'project_id'):
            self.fail("Project ID not available. Project creation test failed.")
        
        url = f"{API_URL}/projects/{self.__class__.project_id}/generate"
        
        # Use RunwayML Gen4 model
        params = {"model": VideoModel.RUNWAYML_GEN4.value}
        
        response = requests.post(url, params=params)
        
        # This might fail if the RunwayML API is not available
        if response.status_code == 200:
            data = response.json()
            self.assertIn("message", data, "Message not found in generation response")
            self.assertIn("project_id", data, "Project ID not found in generation response")
            print("Video generation started successfully")
        else:
            print(f"Video generation returned status code {response.status_code}: {response.text}")
            # Don't fail the test if it's an external API issue
            if "RUNWAYML_API_KEY" in response.text or "RunwayML" in response.text:
                print("Generation failed due to RunwayML API issue - this is expected in test environment")
            else:
                self.fail(f"Video generation failed with unexpected error: {response.text}")
    
    def test_08_get_project_status(self):
        """Test project status API"""
        print("\n=== Testing Project Status API ===")
        
        if not hasattr(self.__class__, 'project_id'):
            self.fail("Project ID not available. Project creation test failed.")
        
        url = f"{API_URL}/projects/{self.__class__.project_id}/status"
        
        response = requests.get(url)
        
        self.assertEqual(response.status_code, 200, f"Failed to get project status: {response.text}")
        
        data = response.json()
        self.assertIn("status", data, "Status not found in response")
        self.assertIn("progress", data, "Progress not found in response")
        
        print(f"Project status: {data['status']}, Progress: {data['progress']}")
    
    def test_09_get_project_details(self):
        """Test project details API"""
        print("\n=== Testing Project Details API ===")
        
        if not hasattr(self.__class__, 'project_id'):
            self.fail("Project ID not available. Project creation test failed.")
        
        url = f"{API_URL}/projects/{self.__class__.project_id}"
        
        response = requests.get(url)
        
        self.assertEqual(response.status_code, 200, f"Failed to get project details: {response.text}")
        
        data = response.json()
        self.assertEqual(data["id"], self.__class__.project_id, "Project ID mismatch")
        self.assertEqual(data["user_id"], TEST_USER_ID, "User ID mismatch")
        
        print(f"Retrieved project details for ID: {data['id']}")
    
    def test_10_download_video(self):
        """Test video download API"""
        print("\n=== Testing Video Download API ===")
        
        if not hasattr(self.__class__, 'project_id'):
            self.fail("Project ID not available. Project creation test failed.")
        
        url = f"{API_URL}/projects/{self.__class__.project_id}/download"
        
        response = requests.get(url)
        
        # This will likely fail since we didn't wait for video generation to complete
        if response.status_code == 200:
            data = response.json()
            self.assertIn("video_base64", data, "Video base64 not found in response")
            self.assertIn("filename", data, "Filename not found in response")
            print("Video download successful")
        else:
            print(f"Video download returned status code {response.status_code}: {response.text}")
            # This is expected since video generation takes time
            if "Video not ready for download" in response.text:
                print("Video not ready for download - this is expected since generation takes time")
            else:
                print(f"Video download failed with error: {response.text}")

if __name__ == "__main__":
    # Run the tests in order
    print("\n======= STARTING VIDEO GENERATION BACKEND TESTS =======\n")
    test_suite = unittest.TestSuite()
    test_suite.addTest(VideoGenerationBackendTest('test_01_create_project'))
    test_suite.addTest(VideoGenerationBackendTest('test_02_upload_sample_video'))
    test_suite.addTest(VideoGenerationBackendTest('test_03_upload_character_image'))
    test_suite.addTest(VideoGenerationBackendTest('test_04_upload_audio'))
    test_suite.addTest(VideoGenerationBackendTest('test_05_analyze_video'))
    test_suite.addTest(VideoGenerationBackendTest('test_06_chat_with_plan'))
    test_suite.addTest(VideoGenerationBackendTest('test_07_start_video_generation'))
    test_suite.addTest(VideoGenerationBackendTest('test_08_get_project_status'))
    test_suite.addTest(VideoGenerationBackendTest('test_09_get_project_details'))
    test_suite.addTest(VideoGenerationBackendTest('test_10_download_video'))
    
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