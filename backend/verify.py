#!/usr/bin/env python3
"""
Quick verification script to test the converted Vercel API endpoints
Run this script to verify that all endpoints are properly configured
"""

import json
import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test lib imports
        sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
        
        from database import get_collection_sync, PROJECT_STATUS, get_database
        from auth import auth_service
        from cloud_storage import cloud_storage_service
        from video_analysis import VideoAnalysisService
        from video_generation import VideoGenerationService, VideoModel
        
        print("✅ All lib imports successful")
        
        # Test database connection
        try:
            db = get_database()
            collection = get_collection_sync('video_projects')
            print("✅ Database connection successful")
        except Exception as e:
            print(f"⚠️  Database connection failed: {e}")
        
        # Test auth service
        try:
            user_id = auth_service.get_current_user()
            print(f"✅ Auth service working (fallback user: {user_id})")
        except Exception as e:
            print(f"⚠️  Auth service failed: {e}")
        
        # Test cloud storage
        try:
            storage_info = cloud_storage_service.get_storage_info()
            print(f"✅ Cloud storage service working: {storage_info['service']}")
        except Exception as e:
            print(f"⚠️  Cloud storage failed: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_api_structure():
    """Test that all API files exist and have proper structure"""
    print("\n🔍 Testing API structure...")
    
    api_files = [
        'projects.py',
        'upload-sample.py',
        'upload-character.py', 
        'upload-audio.py',
        'analyze.py',
        'chat.py',
        'generate.py',
        'status.py',
        'download.py',
        'project-details.py'
    ]
    
    api_dir = os.path.join(os.path.dirname(__file__), 'api')
    missing_files = []
    
    for file in api_files:
        file_path = os.path.join(api_dir, file)
        if os.path.exists(file_path):
            # Check if handler function exists
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'def handler(' in content:
                        print(f"✅ {file} - handler function found")
                    else:
                        print(f"⚠️  {file} - no handler function")
            except Exception as e:
                print(f"⚠️  {file} - error reading file: {e}")
        else:
            missing_files.append(file)
            print(f"❌ {file} - file missing")
    
    if not missing_files:
        print("✅ All API files present")
        return True
    else:
        print(f"❌ Missing files: {missing_files}")
        return False

def test_configuration():
    """Test configuration files"""
    print("\n🔍 Testing configuration...")
    
    required_files = {
        'vercel.json': 'Vercel configuration',
        'requirements.txt': 'Python dependencies',
        'package.json': 'Node.js dependencies', 
        '.env': 'Environment variables',
        'README.md': 'Documentation'
    }
    
    for file, description in required_files.items():
        file_path = os.path.join(os.path.dirname(__file__), file)
        if os.path.exists(file_path):
            print(f"✅ {file} - {description}")
        else:
            print(f"❌ {file} - missing {description}")

def test_environment_variables():
    """Test environment variable requirements"""
    print("\n🔍 Testing environment variables...")
    
    required_vars = {
        'Database': ['MONGO_URL', 'DB_NAME'],
        'AI Services': ['GROQ_API_KEY', 'RUNWAYML_API_KEY', 'GEMINI_API_KEY'],
        'Authentication': ['SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_JWT_SECRET'],
        'Cloud Storage': ['CLOUDFLARE_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET_NAME']
    }
    
    for category, vars in required_vars.items():
        print(f"\n{category}:")
        for var in vars:
            if os.environ.get(var):
                print(f"  ✅ {var} - set")
            else:
                print(f"  ⚠️  {var} - not set (will use fallback/fail)")

def main():
    """Main verification function"""
    print("🚀 AI Video Generation Platform - Vercel Conversion Verification")
    print("=" * 70)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test API structure
    api_ok = test_api_structure()
    
    # Test configuration
    test_configuration()
    
    # Test environment variables
    test_environment_variables()
    
    print("\n" + "=" * 70)
    if imports_ok and api_ok:
        print("🎉 Verification completed! The conversion looks good.")
        print("📋 Next steps:")
        print("   1. Set environment variables in Vercel dashboard")
        print("   2. Deploy using: ./deploy.sh")
        print("   3. Test the live deployment")
    else:
        print("⚠️  Some issues found. Please fix them before deployment.")
    
    print("\n📚 See CONVERSION_SUMMARY.md for detailed deployment instructions")

if __name__ == "__main__":
    main()
