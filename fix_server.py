#!/usr/bin/env python3
import os
import re

def fix_server_py():
    with open('/app/backend/server.py', 'r') as f:
        content = f.read()
    
    # Fix the VideoAnalysisService initialization
    pattern1 = r'self\.llm_chat = LlmChat\([^)]*\)\.with_model\([^)]*\)'
    replacement1 = '''self.llm_chat = LlmChat(
            api_key=os.environ['GEMINI_API_KEY'],
            session_id="video_analysis",
            system_message="""You are an expert video analysis AI. Your task is to analyze sample videos in extreme detail and create comprehensive plans for generating similar videos.

When analyzing a video, provide:
1. Visual Analysis: Describe scenes, objects, characters, lighting, colors, camera movements
2. Audio Analysis: Describe background music, sound effects, voice overs, audio quality
3. Style Analysis: Video style, genre, mood, pacing, transitions
4. Technical Analysis: Resolution, frame rate, duration, aspect ratio
5. Content Analysis: Story, message, theme, target audience

Then create a detailed generation plan with:
1. Scene breakdown with timestamps
2. Visual requirements for each scene
3. Audio requirements
4. Transition effects needed
5. Overall video structure
6. Recommended AI model for generation

Return your analysis in JSON format."""
        )
        self.llm_chat.provider = "google"
        self.llm_chat.model = "gemini-1.5-pro"'''
    
    # Fix the chat interface initialization
    pattern2 = r'chat = LlmChat\([^)]*\)\.with_model\([^)]*\)'
    replacement2 = '''chat = LlmChat(
            api_key=os.environ['GROQ_API_KEY'],
            session_id=f"plan_modification_{project_id}",
            system_message=f"""You are helping to modify a video generation plan. 
            Current plan: {json.dumps(project.generation_plan, indent=2)}
            
            The user wants to make changes to this plan. Listen to their requests and provide an updated plan.
            Always return your response in JSON format with 'response' and 'updated_plan' keys."""
        )
        chat.provider = "groq"
        chat.model = "llama3-70b-8192"'''
    
    # Apply the replacements
    content = re.sub(pattern1, replacement1, content)
    content = re.sub(pattern2, replacement2, content)
    
    with open('/app/backend/server.py', 'w') as f:
        f.write(content)
    
    print("Server.py has been fixed.")

if __name__ == "__main__":
    fix_server_py()
