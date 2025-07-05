#!/bin/bash

# Set the API URL
API_URL="http://0.0.0.0:8001/api"
USER_ID="test_user_shell_$(date +%s)"

echo "======= STARTING VIDEO GENERATION BACKEND TESTS ======="
echo "Using API URL: $API_URL"
echo "Using test user ID: $USER_ID"

# Test 1: Create Project
echo -e "\n=== Testing Project Creation API ==="
PROJECT_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "{\"user_id\": \"$USER_ID\"}" $API_URL/projects)
PROJECT_ID=$(echo $PROJECT_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -n "$PROJECT_ID" ]; then
    echo "Created project with ID: $PROJECT_ID"
    echo "✅ Project creation API works"
else
    echo "❌ Project creation API failed"
    echo "Response: $PROJECT_RESPONSE"
    exit 1
fi

# Create sample files
mkdir -p /app/backend
echo "DUMMY VIDEO CONTENT" > /app/backend/sample_video.mp4
echo "DUMMY IMAGE CONTENT" > /app/backend/sample_image.jpg
echo "DUMMY AUDIO CONTENT" > /app/backend/sample_audio.mp3

# Test 2: Upload Sample Video
echo -e "\n=== Testing Sample Video Upload API ==="
UPLOAD_RESPONSE=$(curl -s -X POST -F "file=@/app/backend/sample_video.mp4;type=video/mp4" $API_URL/projects/$PROJECT_ID/upload-sample)

if echo $UPLOAD_RESPONSE | grep -q "success"; then
    echo "Upload response: $UPLOAD_RESPONSE"
    echo "✅ Sample video upload API works"
else
    echo "❌ Sample video upload API failed"
    echo "Response: $UPLOAD_RESPONSE"
fi

# Test 3: Upload Character Image
echo -e "\n=== Testing Character Image Upload API ==="
UPLOAD_RESPONSE=$(curl -s -X POST -F "file=@/app/backend/sample_image.jpg;type=image/jpeg" $API_URL/projects/$PROJECT_ID/upload-character)

if echo $UPLOAD_RESPONSE | grep -q "success"; then
    echo "Upload response: $UPLOAD_RESPONSE"
    echo "✅ Character image upload API works"
else
    echo "❌ Character image upload API failed"
    echo "Response: $UPLOAD_RESPONSE"
fi

# Test 4: Upload Audio
echo -e "\n=== Testing Audio Upload API ==="
UPLOAD_RESPONSE=$(curl -s -X POST -F "file=@/app/backend/sample_audio.mp3;type=audio/mpeg" $API_URL/projects/$PROJECT_ID/upload-audio)

if echo $UPLOAD_RESPONSE | grep -q "success"; then
    echo "Upload response: $UPLOAD_RESPONSE"
    echo "✅ Audio upload API works"
else
    echo "❌ Audio upload API failed"
    echo "Response: $UPLOAD_RESPONSE"
fi

# Test 5: Analyze Video
echo -e "\n=== Testing Video Analysis API ==="
ANALYSIS_RESPONSE=$(curl -s -X POST $API_URL/projects/$PROJECT_ID/analyze)

if echo $ANALYSIS_RESPONSE | grep -q "analysis"; then
    echo "Video analysis completed successfully"
    echo "✅ Video analysis API works"
else
    echo "❌ Video analysis API failed"
    echo "Response: $ANALYSIS_RESPONSE"
    
    if echo $ANALYSIS_RESPONSE | grep -q "File attachments are only supported with Gemini provider"; then
        echo -e "\nDETAILED ERROR: The error suggests that the code is trying to use a provider other than Gemini for file attachments."
        echo "In server.py, the VideoAnalysisService is configured to use Gemini (line 152), but there might be an issue with how the provider is being used."
        echo "This could be due to a conflict in the emergentintegrations package or how it's being initialized."
    fi
fi

# Test 6: Chat with Plan
echo -e "\n=== Testing Chat API ==="
CHAT_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "{\"project_id\": \"$PROJECT_ID\", \"message\": \"Can you make the video more vibrant and colorful?\", \"user_id\": \"$USER_ID\"}" $API_URL/projects/$PROJECT_ID/chat)

if echo $CHAT_RESPONSE | grep -q "response"; then
    echo "Chat API responded successfully"
    echo "✅ Chat API works"
else
    echo "❌ Chat API failed"
    echo "Response: $CHAT_RESPONSE"
    
    if echo $CHAT_RESPONSE | grep -q "AuthenticationError" && echo $CHAT_RESPONSE | grep -q "API key"; then
        echo -e "\nDETAILED ERROR: The error suggests an issue with the API key authentication."
        echo "In server.py, the chat interface is configured to use Groq with the llama3-70b-8192 model (line 626)."
        echo "The API key might be incorrect or in the wrong format. Check the GROQ_API_KEY in the .env file."
    fi
fi

# Test 7: Start Video Generation
echo -e "\n=== Testing Video Generation API ==="
GENERATION_RESPONSE=$(curl -s -X POST "$API_URL/projects/$PROJECT_ID/generate?model=runwayml_gen4")

if echo $GENERATION_RESPONSE | grep -q "message" && echo $GENERATION_RESPONSE | grep -q "project_id"; then
    echo "Video generation started successfully"
    echo "✅ Video generation API works"
else
    echo "❌ Video generation API failed"
    echo "Response: $GENERATION_RESPONSE"
    
    if echo $GENERATION_RESPONSE | grep -q "No generation plan available"; then
        echo -e "\nDETAILED ERROR: The error indicates that no generation plan is available."
        echo "This is expected because the video analysis step failed, which is responsible for creating the generation plan."
        echo "Fix the video analysis issue first, then this endpoint should work correctly."
    fi
fi

# Test 8: Get Project Status
echo -e "\n=== Testing Project Status API ==="
STATUS_RESPONSE=$(curl -s -X GET $API_URL/projects/$PROJECT_ID/status)

if echo $STATUS_RESPONSE | grep -q "status" && echo $STATUS_RESPONSE | grep -q "progress"; then
    STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*' | cut -d'"' -f4)
    PROGRESS=$(echo $STATUS_RESPONSE | grep -o '"progress":[^,}]*' | cut -d':' -f2)
    echo "Project status: $STATUS, Progress: $PROGRESS"
    echo "✅ Project status API works"
else
    echo "❌ Project status API failed"
    echo "Response: $STATUS_RESPONSE"
fi

# Test 9: Get Project Details
echo -e "\n=== Testing Project Details API ==="
DETAILS_RESPONSE=$(curl -s -X GET $API_URL/projects/$PROJECT_ID)

if echo $DETAILS_RESPONSE | grep -q "\"id\":\"$PROJECT_ID\"" && echo $DETAILS_RESPONSE | grep -q "\"user_id\":\"$USER_ID\""; then
    echo "Retrieved project details for ID: $PROJECT_ID"
    echo "✅ Project details API works"
else
    echo "❌ Project details API failed"
    echo "Response: $DETAILS_RESPONSE"
fi

# Test 10: Download Video
echo -e "\n=== Testing Video Download API ==="
DOWNLOAD_RESPONSE=$(curl -s -X GET $API_URL/projects/$PROJECT_ID/download)

if echo $DOWNLOAD_RESPONSE | grep -q "Video not ready for download"; then
    echo "Video not ready for download yet (expected at this stage)"
    echo "✅ Video download API works (returned expected 'not ready' response)"
elif echo $DOWNLOAD_RESPONSE | grep -q "video_base64" && echo $DOWNLOAD_RESPONSE | grep -q "filename"; then
    echo "Video download successful"
    echo "✅ Video download API works"
else
    echo "❌ Video download API failed"
    echo "Response: $DOWNLOAD_RESPONSE"
    
    if echo $DOWNLOAD_RESPONSE | grep -q "Video not ready for download"; then
        echo -e "\nDETAILED ERROR: The error indicates that the video is not ready for download."
        echo "This is expected because the video generation process failed due to the issues with the video analysis and generation steps."
        echo "Fix the video analysis and generation issues first, then this endpoint should work correctly."
    fi
fi

echo -e "\n======= TEST RESULTS SUMMARY ======="
echo "All tests completed. Check the output above for details."
echo "======= END OF TESTS ======="