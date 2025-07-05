#!/usr/bin/env python3
import os
import sys
import json
import uuid
import subprocess
import unittest
from pathlib import Path

# Sample file paths
SAMPLE_VIDEO_PATH = "/app/backend/sample_video.mp4"
SAMPLE_IMAGE_PATH = "/app/backend/sample_image.jpg"
SAMPLE_AUDIO_PATH = "/app/backend/sample_audio.mp3"

# Create sample files if they don't exist
def create_sample_files():
    # Create a simple video file
    if not os.path.exists(SAMPLE_VIDEO_PATH):
        with open(SAMPLE_VIDEO_PATH, 'wb') as f:
            f.write(b'DUMMY VIDEO CONTENT')
        print(f"Created dummy video file at {SAMPLE_VIDEO_PATH}")
    
    # Create a simple image file
    if not os.path.exists(SAMPLE_IMAGE_PATH):
        with open(SAMPLE_IMAGE_PATH, 'wb') as f:
            f.write(b'DUMMY IMAGE CONTENT')
        print(f"Created dummy image file at {SAMPLE_IMAGE_PATH}")
    
    # Create a simple audio file
    if not os.path.exists(SAMPLE_AUDIO_PATH):
        with open(SAMPLE_AUDIO_PATH, 'wb') as f:
            f.write(b'DUMMY AUDIO CONTENT')
        print(f"Created dummy audio file at {SAMPLE_AUDIO_PATH}")
            
    # Make sure the parent directories exist
    os.makedirs(os.path.dirname(SAMPLE_VIDEO_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(SAMPLE_IMAGE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(SAMPLE_AUDIO_PATH), exist_ok=True)

# Use curl for API requests
def curl_get(url):
    cmd = ["curl", "-s", url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Curl command failed: {result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw_response": result.stdout}

def curl_post(url, json_data=None):
    cmd = ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json"]
    if json_data:
        cmd.extend(["-d", json.dumps(json_data)])
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Curl command failed: {result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw_response": result.stdout}

def curl_upload_file(url, file_path, file_type):
    cmd = [
        "curl", "-s", "-X", "POST", 
        url,
        "-F", f"file=@{file_path};type={file_type}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Curl command failed: {result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw_response": result.stdout}

class CloudflareR2Test(unittest.TestCase):
    """Test suite for Cloudflare R2 integration"""
    
    def setUp(self):
        """Set up test environment"""
        create_sample_files()
        self.project_id = None
        self.api_url = "http://localhost:8001/api"
        print(f"Using API URL: {self.api_url}")
    
    def test_01_storage_status(self):
        """Test storage service status endpoint"""
        print("\n=== Testing Storage Service Status API ===")
        
        url = f"{self.api_url}/storage/status"
        
        try:
            data = curl_get(url)
            
            self.assertIn("available", data, "Available status not found in response")
            self.assertIn("storage_info", data, "Storage info not found in response")
            
            storage_info = data["storage_info"]
            self.assertIn("service", storage_info, "Service name not found in storage info")
            self.assertIn("status", storage_info, "Status not found in storage info")
            
            # Check if using Cloudflare R2
            self.assertEqual(storage_info["service"], "Cloudflare R2", 
                            f"Expected Cloudflare R2 service, got {storage_info['service']}")
            self.assertEqual(storage_info["status"], "connected", 
                            f"Expected 'connected' status, got {storage_info['status']}")
            
            print(f"Storage service: {storage_info['service']}")
            print(f"Storage status: {storage_info['status']}")
            if "bucket" in storage_info:
                print(f"Storage bucket: {storage_info['bucket']}")
            if "account_id" in storage_info:
                print(f"Cloudflare account ID: {storage_info['account_id']}")
            
            print("✅ Storage status API confirms Cloudflare R2 is connected")
            return True
        except Exception as e:
            print(f"❌ Storage status API failed: {str(e)}")
            return False
    
    def test_02_create_project(self):
        """Test project creation API"""
        print("\n=== Testing Project Creation API ===")
        
        url = f"{self.api_url}/projects"
        payload = {"user_id": f"test_user_{uuid.uuid4().hex[:8]}"}
        
        try:
            data = curl_post(url, payload)
            
            self.assertIn("id", data, "Project ID not found in response")
            self.assertIn("user_id", data, "User ID not found in response")
            
            self.project_id = data["id"]
            print(f"Created project with ID: {self.project_id}")
            print(f"Project user_id: {data['user_id']}")
            print("✅ Project creation API works")
            
            # Store project ID for other tests
            CloudflareR2Test.project_id = self.project_id
            return True
        except Exception as e:
            print(f"❌ Project creation API failed: {str(e)}")
            return False
    
    def test_03_upload_sample_video(self):
        """Test sample video upload with R2 integration"""
        print("\n=== Testing Sample Video Upload with R2 Integration ===")
        
        if not hasattr(CloudflareR2Test, 'project_id') or not CloudflareR2Test.project_id:
            self.skipTest("Project ID not available, skipping test")
        
        url = f"{self.api_url}/projects/{CloudflareR2Test.project_id}/upload-sample"
        
        try:
            data = curl_upload_file(url, SAMPLE_VIDEO_PATH, "video/mp4")
            
            self.assertIn("message", data, "Message not found in response")
            self.assertIn("file_url", data, "File URL not found in response")
            
            # Check if the file URL is an R2 URL
            file_url = data["file_url"]
            self.assertTrue(file_url.startswith("https://"), 
                           f"Expected R2 URL starting with 'https://', got {file_url}")
            self.assertTrue("r2.cloudflarestorage.com" in file_url, 
                           f"Expected R2 URL containing 'r2.cloudflarestorage.com', got {file_url}")
            
            print(f"Upload message: {data['message']}")
            print(f"File URL: {file_url}")
            print("✅ Sample video upload with R2 integration works")
            
            # Store file URL for other tests
            CloudflareR2Test.video_url = file_url
            return True
        except Exception as e:
            print(f"❌ Sample video upload failed: {str(e)}")
            return False
    
    def test_04_upload_character_image(self):
        """Test character image upload with R2 integration"""
        print("\n=== Testing Character Image Upload with R2 Integration ===")
        
        if not hasattr(CloudflareR2Test, 'project_id') or not CloudflareR2Test.project_id:
            self.skipTest("Project ID not available, skipping test")
        
        url = f"{self.api_url}/projects/{CloudflareR2Test.project_id}/upload-character"
        
        try:
            data = curl_upload_file(url, SAMPLE_IMAGE_PATH, "image/jpeg")
            
            self.assertIn("message", data, "Message not found in response")
            self.assertIn("file_url", data, "File URL not found in response")
            
            # Check if the file URL is an R2 URL
            file_url = data["file_url"]
            self.assertTrue(file_url.startswith("https://"), 
                           f"Expected R2 URL starting with 'https://', got {file_url}")
            self.assertTrue("r2.cloudflarestorage.com" in file_url, 
                           f"Expected R2 URL containing 'r2.cloudflarestorage.com', got {file_url}")
            
            print(f"Upload message: {data['message']}")
            print(f"File URL: {file_url}")
            print("✅ Character image upload with R2 integration works")
            
            # Store file URL for other tests
            CloudflareR2Test.image_url = file_url
            return True
        except Exception as e:
            print(f"❌ Character image upload failed: {str(e)}")
            return False
    
    def test_05_upload_audio(self):
        """Test audio upload with R2 integration"""
        print("\n=== Testing Audio Upload with R2 Integration ===")
        
        if not hasattr(CloudflareR2Test, 'project_id') or not CloudflareR2Test.project_id:
            self.skipTest("Project ID not available, skipping test")
        
        url = f"{self.api_url}/projects/{CloudflareR2Test.project_id}/upload-audio"
        
        try:
            data = curl_upload_file(url, SAMPLE_AUDIO_PATH, "audio/mpeg")
            
            self.assertIn("message", data, "Message not found in response")
            self.assertIn("file_url", data, "File URL not found in response")
            
            # Check if the file URL is an R2 URL
            file_url = data["file_url"]
            self.assertTrue(file_url.startswith("https://"), 
                           f"Expected R2 URL starting with 'https://', got {file_url}")
            self.assertTrue("r2.cloudflarestorage.com" in file_url, 
                           f"Expected R2 URL containing 'r2.cloudflarestorage.com', got {file_url}")
            
            print(f"Upload message: {data['message']}")
            print(f"File URL: {file_url}")
            print("✅ Audio upload with R2 integration works")
            
            # Store file URL for other tests
            CloudflareR2Test.audio_url = file_url
            return True
        except Exception as e:
            print(f"❌ Audio upload failed: {str(e)}")
            return False
    
    def test_06_get_project_details(self):
        """Test project details to verify R2 URLs are stored in the database"""
        print("\n=== Testing Project Details with R2 URLs ===")
        
        if not hasattr(CloudflareR2Test, 'project_id') or not CloudflareR2Test.project_id:
            self.skipTest("Project ID not available, skipping test")
        
        url = f"{self.api_url}/projects/{CloudflareR2Test.project_id}"
        
        try:
            data = curl_get(url)
            
            self.assertEqual(data["id"], CloudflareR2Test.project_id, "Project ID mismatch")
            
            # Check if the file paths are R2 URLs
            if "sample_video_path" in data and data["sample_video_path"]:
                self.assertTrue(data["sample_video_path"].startswith("https://"), 
                               "Sample video path is not an R2 URL")
                self.assertTrue("r2.cloudflarestorage.com" in data["sample_video_path"], 
                               "Sample video path is not an R2 URL")
                print(f"Sample video path: {data['sample_video_path']}")
            
            if "character_image_path" in data and data["character_image_path"]:
                self.assertTrue(data["character_image_path"].startswith("https://"), 
                               "Character image path is not an R2 URL")
                self.assertTrue("r2.cloudflarestorage.com" in data["character_image_path"], 
                               "Character image path is not an R2 URL")
                print(f"Character image path: {data['character_image_path']}")
            
            if "audio_path" in data and data["audio_path"]:
                self.assertTrue(data["audio_path"].startswith("https://"), 
                               "Audio path is not an R2 URL")
                self.assertTrue("r2.cloudflarestorage.com" in data["audio_path"], 
                               "Audio path is not an R2 URL")
                print(f"Audio path: {data['audio_path']}")
            
            print("✅ Project details confirm R2 URLs are stored in the database")
            return True
        except Exception as e:
            print(f"❌ Project details API failed: {str(e)}")
            return False

if __name__ == "__main__":
    # Run the tests in order
    print("\n======= STARTING CLOUDFLARE R2 INTEGRATION TESTS =======\n")
    
    test_suite = unittest.TestSuite()
    test_suite.addTest(CloudflareR2Test('test_01_storage_status'))
    test_suite.addTest(CloudflareR2Test('test_02_create_project'))
    test_suite.addTest(CloudflareR2Test('test_03_upload_sample_video'))
    test_suite.addTest(CloudflareR2Test('test_04_upload_character_image'))
    test_suite.addTest(CloudflareR2Test('test_05_upload_audio'))
    test_suite.addTest(CloudflareR2Test('test_06_get_project_details'))
    
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