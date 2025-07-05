#!/usr/bin/env python3
import os
import sys
import json
import uuid
import time
import base64
import requests
import unittest
import subprocess
from enum import Enum
from typing import Dict, Any, Optional
from pathlib import Path

# Get the backend URL from the frontend .env file
def get_backend_url():
    # Read the frontend .env file to get the backend URL
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.strip().split('=', 1)[1].strip('"\'')
                    return f"{backend_url}"
        # Fallback to local URL if not found
        return "http://0.0.0.0:8001"
    except Exception as e:
        print(f"Error reading backend URL: {str(e)}")
        return "http://0.0.0.0:8001"

BACKEND_URL = get_backend_url()
if not BACKEND_URL:
    print("Error: Could not find backend URL")
    sys.exit(1)

API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Test user credentials
TEST_EMAIL = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "Test@Password123"
TEST_EMAIL2 = f"test_user2_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD2 = "Test@Password123"

class AuthenticationTest(unittest.TestCase):
    """Test suite for the Authentication API"""
    
    def setUp(self):
        """Set up test environment"""
        self.access_token = None
        self.user_id = None
        self.access_token2 = None
        self.user_id2 = None
        print(f"Using test email: {TEST_EMAIL}")
    
    def test_01_register_user(self):
        """Test user registration API"""
        print("\n=== Testing User Registration API ===")
        
        url = f"{API_URL}/auth/register"
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            self.assertIn("message", data, "Message not found in response")
            self.assertIn("user", data, "User data not found in response")
            self.assertIn("access_token", data, "Access token not found in response")
            
            # Store user ID and access token for other tests
            AuthenticationTest.user_id = data["user"]["id"]
            AuthenticationTest.access_token = data["access_token"]
            
            print(f"Registered user with ID: {AuthenticationTest.user_id}")
            print(f"Access token: {AuthenticationTest.access_token[:20]}...")
            print("✅ User registration API works")
            return True
        except Exception as e:
            print(f"❌ User registration API failed: {str(e)}")
            return False
    
    def test_02_register_second_user(self):
        """Test registering a second user for cross-user tests"""
        print("\n=== Testing Second User Registration ===")
        
        url = f"{API_URL}/auth/register"
        payload = {
            "email": TEST_EMAIL2,
            "password": TEST_PASSWORD2
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            self.assertIn("message", data, "Message not found in response")
            self.assertIn("user", data, "User data not found in response")
            self.assertIn("access_token", data, "Access token not found in response")
            
            # Store user ID and access token for other tests
            AuthenticationTest.user_id2 = data["user"]["id"]
            AuthenticationTest.access_token2 = data["access_token"]
            
            print(f"Registered second user with ID: {AuthenticationTest.user_id2}")
            print(f"Second user access token: {AuthenticationTest.access_token2[:20]}...")
            print("✅ Second user registration successful")
            return True
        except Exception as e:
            print(f"❌ Second user registration failed: {str(e)}")
            return False
    
    def test_03_login_user(self):
        """Test user login API"""
        print("\n=== Testing User Login API ===")
        
        url = f"{API_URL}/auth/login"
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            self.assertIn("message", data, "Message not found in response")
            self.assertIn("user", data, "User data not found in response")
            self.assertIn("access_token", data, "Access token not found in response")
            
            # Verify user ID matches the registered user
            self.assertEqual(data["user"]["id"], AuthenticationTest.user_id, "User ID mismatch")
            
            # Update access token
            AuthenticationTest.access_token = data["access_token"]
            
            print(f"Logged in user with ID: {data['user']['id']}")
            print(f"New access token: {AuthenticationTest.access_token[:20]}...")
            print("✅ User login API works")
            return True
        except Exception as e:
            print(f"❌ User login API failed: {str(e)}")
            return False
    
    def test_04_get_current_user(self):
        """Test getting current user info"""
        print("\n=== Testing Get Current User API ===")
        
        if not hasattr(AuthenticationTest, 'access_token') or not AuthenticationTest.access_token:
            self.skipTest("Access token not available, skipping test")
        
        url = f"{API_URL}/auth/me"
        headers = {"Authorization": f"Bearer {AuthenticationTest.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            self.assertIn("id", data, "User ID not found in response")
            self.assertIn("email", data, "Email not found in response")
            
            # Verify user ID matches the registered user
            self.assertEqual(data["id"], AuthenticationTest.user_id, "User ID mismatch")
            self.assertEqual(data["email"], TEST_EMAIL, "Email mismatch")
            
            print(f"Retrieved user info for ID: {data['id']}")
            print(f"User email: {data['email']}")
            print("✅ Get current user API works")
            return True
        except Exception as e:
            print(f"❌ Get current user API failed: {str(e)}")
            return False
    
    def test_05_get_current_user_no_auth(self):
        """Test getting current user info without authentication"""
        print("\n=== Testing Get Current User API Without Authentication ===")
        
        url = f"{API_URL}/auth/me"
        
        try:
            response = requests.get(url)
            
            # Should fail with 401 Unauthorized
            self.assertEqual(response.status_code, 401, "Expected 401 Unauthorized")
            
            print("Request failed with status code:", response.status_code)
            print("Response:", response.text)
            print("✅ Get current user API correctly requires authentication")
            return True
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            return False
    
    def test_06_logout_user(self):
        """Test user logout API"""
        print("\n=== Testing User Logout API ===")
        
        if not hasattr(AuthenticationTest, 'access_token') or not AuthenticationTest.access_token:
            self.skipTest("Access token not available, skipping test")
        
        url = f"{API_URL}/auth/logout"
        headers = {"Authorization": f"Bearer {AuthenticationTest.access_token}"}
        
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            self.assertIn("message", data, "Message not found in response")
            self.assertEqual(data["message"], "Logout successful", "Unexpected message")
            
            print("Logout successful")
            print("✅ User logout API works")
            return True
        except Exception as e:
            print(f"❌ User logout API failed: {str(e)}")
            return False

class ProjectManagementTest(unittest.TestCase):
    """Test suite for the Project Management API with Authentication"""
    
    def setUp(self):
        """Set up test environment"""
        self.project_id = None
        self.project_id2 = None
        
        # Use the access token from the authentication tests
        if hasattr(AuthenticationTest, 'access_token') and AuthenticationTest.access_token:
            self.access_token = AuthenticationTest.access_token
            self.user_id = AuthenticationTest.user_id
            print(f"Using access token from authentication tests")
        else:
            # Login to get a token if not available
            print("No access token available, logging in...")
            url = f"{API_URL}/auth/login"
            payload = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                self.access_token = data["access_token"]
                self.user_id = data["user"]["id"]
                print(f"Logged in with user ID: {self.user_id}")
            except Exception as e:
                print(f"Failed to login: {str(e)}")
                self.access_token = None
                self.user_id = None
        
        # Get the second user's access token
        if hasattr(AuthenticationTest, 'access_token2') and AuthenticationTest.access_token2:
            self.access_token2 = AuthenticationTest.access_token2
            self.user_id2 = AuthenticationTest.user_id2
            print(f"Using second user's access token from authentication tests")
        else:
            # Login to get a token if not available
            print("No second user access token available, logging in...")
            url = f"{API_URL}/auth/login"
            payload = {
                "email": TEST_EMAIL2,
                "password": TEST_PASSWORD2
            }
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                self.access_token2 = data["access_token"]
                self.user_id2 = data["user"]["id"]
                print(f"Logged in with second user ID: {self.user_id2}")
            except Exception as e:
                print(f"Failed to login as second user: {str(e)}")
                self.access_token2 = None
                self.user_id2 = None
    
    def test_01_create_project(self):
        """Test project creation API with authentication"""
        print("\n=== Testing Project Creation API with Authentication ===")
        
        if not self.access_token:
            self.skipTest("Access token not available, skipping test")
        
        url = f"{API_URL}/projects"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {}  # No need to specify user_id, it comes from the token
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            self.assertIn("id", data, "Project ID not found in response")
            self.assertIn("user_id", data, "User ID not found in response")
            
            # Verify the project is associated with the authenticated user
            self.assertEqual(data["user_id"], self.user_id, "Project not associated with authenticated user")
            
            self.project_id = data["id"]
            print(f"Created project with ID: {self.project_id}")
            print(f"Project user_id: {data['user_id']} (from authentication)")
            print("✅ Project creation API works with authentication")
            
            # Store project ID for other tests
            ProjectManagementTest.project_id = self.project_id
            return True
        except Exception as e:
            print(f"❌ Project creation API failed: {str(e)}")
            return False
    
    def test_02_create_project_second_user(self):
        """Test project creation for second user"""
        print("\n=== Testing Project Creation for Second User ===")
        
        if not self.access_token2:
            self.skipTest("Second user access token not available, skipping test")
        
        url = f"{API_URL}/projects"
        headers = {"Authorization": f"Bearer {self.access_token2}"}
        payload = {}  # No need to specify user_id, it comes from the token
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            self.assertIn("id", data, "Project ID not found in response")
            self.assertIn("user_id", data, "User ID not found in response")
            
            # Verify the project is associated with the second user
            self.assertEqual(data["user_id"], self.user_id2, "Project not associated with second user")
            
            self.project_id2 = data["id"]
            print(f"Created project for second user with ID: {self.project_id2}")
            print(f"Project user_id: {data['user_id']} (from authentication)")
            print("✅ Project creation works for second user")
            
            # Store project ID for other tests
            ProjectManagementTest.project_id2 = self.project_id2
            return True
        except Exception as e:
            print(f"❌ Project creation for second user failed: {str(e)}")
            return False
    
    def test_03_list_projects(self):
        """Test listing user's projects"""
        print("\n=== Testing List User Projects API ===")
        
        if not self.access_token:
            self.skipTest("Access token not available, skipping test")
        
        url = f"{API_URL}/projects"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            self.assertIn("projects", data, "Projects list not found in response")
            
            # Check if our project is in the list
            project_ids = [p["id"] for p in data["projects"]]
            self.assertIn(self.project_id, project_ids, "Created project not found in user's projects list")
            
            print(f"Retrieved {len(data['projects'])} projects for user")
            print(f"Project IDs: {project_ids}")
            print("✅ List user projects API works")
            return True
        except Exception as e:
            print(f"❌ List user projects API failed: {str(e)}")
            return False
    
    def test_04_list_projects_no_auth(self):
        """Test listing projects without authentication"""
        print("\n=== Testing List Projects API Without Authentication ===")
        
        url = f"{API_URL}/projects"
        
        try:
            response = requests.get(url)
            
            # Should fail with 401 Unauthorized
            self.assertEqual(response.status_code, 401, "Expected 401 Unauthorized")
            
            print("Request failed with status code:", response.status_code)
            print("Response:", response.text)
            print("✅ List projects API correctly requires authentication")
            return True
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            return False
    
    def test_05_access_other_user_project(self):
        """Test accessing another user's project"""
        print("\n=== Testing Access to Another User's Project ===")
        
        if not self.access_token or not hasattr(ProjectManagementTest, 'project_id2') or not ProjectManagementTest.project_id2:
            self.skipTest("Access token or second user's project ID not available, skipping test")
        
        url = f"{API_URL}/projects/{ProjectManagementTest.project_id2}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            
            # Should fail with 404 Not Found (or 403 Forbidden)
            self.assertIn(response.status_code, [403, 404], "Expected 403 Forbidden or 404 Not Found")
            
            print("Request failed with status code:", response.status_code)
            print("Response:", response.text)
            print("✅ Project access correctly prevents cross-user access")
            return True
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            return False
    
    def test_06_delete_project(self):
        """Test deleting user's project"""
        print("\n=== Testing Delete Project API ===")
        
        if not self.access_token or not hasattr(ProjectManagementTest, 'project_id') or not ProjectManagementTest.project_id:
            self.skipTest("Access token or project ID not available, skipping test")
        
        url = f"{API_URL}/projects/{ProjectManagementTest.project_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            self.assertIn("message", data, "Message not found in response")
            self.assertEqual(data["message"], "Project deleted successfully", "Unexpected message")
            
            print("Project deleted successfully")
            print("✅ Delete project API works")
            return True
        except Exception as e:
            print(f"❌ Delete project API failed: {str(e)}")
            return False
    
    def test_07_delete_other_user_project(self):
        """Test deleting another user's project"""
        print("\n=== Testing Delete Another User's Project ===")
        
        if not self.access_token or not hasattr(ProjectManagementTest, 'project_id2') or not ProjectManagementTest.project_id2:
            self.skipTest("Access token or second user's project ID not available, skipping test")
        
        url = f"{API_URL}/projects/{ProjectManagementTest.project_id2}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.delete(url, headers=headers)
            
            # Should fail with 404 Not Found (or 403 Forbidden)
            self.assertIn(response.status_code, [403, 404], "Expected 403 Forbidden or 404 Not Found")
            
            print("Request failed with status code:", response.status_code)
            print("Response:", response.text)
            print("✅ Delete project API correctly prevents cross-user deletion")
            return True
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            return False

if __name__ == "__main__":
    # Run the tests in order
    print("\n======= STARTING AUTHENTICATION AND PROJECT MANAGEMENT TESTS =======\n")
    
    # Authentication Tests
    auth_suite = unittest.TestSuite()
    auth_suite.addTest(AuthenticationTest('test_01_register_user'))
    auth_suite.addTest(AuthenticationTest('test_02_register_second_user'))
    auth_suite.addTest(AuthenticationTest('test_03_login_user'))
    auth_suite.addTest(AuthenticationTest('test_04_get_current_user'))
    auth_suite.addTest(AuthenticationTest('test_05_get_current_user_no_auth'))
    auth_suite.addTest(AuthenticationTest('test_06_logout_user'))
    
    # Project Management Tests
    project_suite = unittest.TestSuite()
    project_suite.addTest(ProjectManagementTest('test_01_create_project'))
    project_suite.addTest(ProjectManagementTest('test_02_create_project_second_user'))
    project_suite.addTest(ProjectManagementTest('test_03_list_projects'))
    project_suite.addTest(ProjectManagementTest('test_04_list_projects_no_auth'))
    project_suite.addTest(ProjectManagementTest('test_05_access_other_user_project'))
    project_suite.addTest(ProjectManagementTest('test_06_delete_project'))
    project_suite.addTest(ProjectManagementTest('test_07_delete_other_user_project'))
    
    # Run all test suites
    runner = unittest.TextTestRunner(verbosity=2)
    
    print("\n=== AUTHENTICATION TESTS ===")
    auth_result = runner.run(auth_suite)
    
    print("\n=== PROJECT MANAGEMENT TESTS ===")
    project_result = runner.run(project_suite)
    
    # Combine results
    total_tests = auth_result.testsRun + project_result.testsRun
    total_errors = len(auth_result.errors) + len(project_result.errors)
    total_failures = len(auth_result.failures) + len(project_result.failures)
    
    print("\n======= TEST RESULTS SUMMARY =======")
    print(f"Tests run: {total_tests}")
    print(f"Errors: {total_errors}")
    print(f"Failures: {total_failures}")
    
    if auth_result.errors or project_result.errors:
        print("\n--- ERRORS ---")
        for test, error in auth_result.errors + project_result.errors:
            print(f"\n{test}:\n{error}")
    
    if auth_result.failures or project_result.failures:
        print("\n--- FAILURES ---")
        for test, failure in auth_result.failures + project_result.failures:
            print(f"\n{test}:\n{failure}")
    
    print("\n======= END OF TESTS =======\n")