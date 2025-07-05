#!/usr/bin/env python3
import os

def fix_server_py():
    with open('/app/backend/server.py', 'r') as f:
        content = f.readlines()
    
    # Find the VideoAnalysisService.__init__ method
    in_init = False
    init_start = 0
    init_end = 0
    
    for i, line in enumerate(content):
        if "def __init__(self):" in line and "VideoAnalysisService" in content[i-1]:
            in_init = True
            init_start = i
        elif in_init and "def " in line:
            init_end = i
            break
    
    if init_end == 0:  # If we didn't find the end, assume it's the next method
        for i in range(init_start + 1, len(content)):
            if "    def " in content[i]:
                init_end = i
                break
    
    # Replace the init method
    new_init = [
        "    def __init__(self):\n",
        "        self.llm_chat = LlmChat(\n",
        "            api_key=os.environ['GEMINI_API_KEY'],\n",
        "            session_id=\"video_analysis\",\n",
        "            system_message=\"\"\"You are an expert video analysis AI. Your task is to analyze sample videos in extreme detail and create comprehensive plans for generating similar videos.\n",
        "\n",
        "When analyzing a video, provide:\n",
        "1. Visual Analysis: Describe scenes, objects, characters, lighting, colors, camera movements\n",
        "2. Audio Analysis: Describe background music, sound effects, voice overs, audio quality\n",
        "3. Style Analysis: Video style, genre, mood, pacing, transitions\n",
        "4. Technical Analysis: Resolution, frame rate, duration, aspect ratio\n",
        "5. Content Analysis: Story, message, theme, target audience\n",
        "\n",
        "Then create a detailed generation plan with:\n",
        "1. Scene breakdown with timestamps\n",
        "2. Visual requirements for each scene\n",
        "3. Audio requirements\n",
        "4. Transition effects needed\n",
        "5. Overall video structure\n",
        "6. Recommended AI model for generation\n",
        "\n",
        "Return your analysis in JSON format.\"\"\"\n",
        "        )\n",
        "        # Set provider and model manually after initialization\n",
        "        self.llm_chat.provider = \"google\"\n",
        "        self.llm_chat.model = \"gemini-1.5-pro\"\n",
    ]
    
    # Find the chat_with_plan method
    chat_method_start = 0
    chat_init_start = 0
    chat_init_end = 0
    
    for i, line in enumerate(content):
        if "async def chat_with_plan" in line:
            chat_method_start = i
            break
    
    if chat_method_start > 0:
        for i in range(chat_method_start, len(content)):
            if "chat = LlmChat(" in line:
                chat_init_start = i
                break
        
        if chat_init_start > 0:
            for i in range(chat_init_start, len(content)):
                if ").with_model(" in content[i]:
                    chat_init_end = i + 1
                    break
                elif ")" in content[i] and chat_init_end == 0:
                    chat_init_end = i + 1
                    break
    
    # Replace the chat initialization
    new_chat_init = [
        "        chat = LlmChat(\n",
        "            api_key=os.environ['GROQ_API_KEY'],\n",
        "            session_id=f\"plan_modification_{project_id}\",\n",
        "            system_message=f\"\"\"You are helping to modify a video generation plan. \n",
        "            Current plan: {json.dumps(project.generation_plan, indent=2)}\n",
        "            \n",
        "            The user wants to make changes to this plan. Listen to their requests and provide an updated plan.\n",
        "            Always return your response in JSON format with 'response' and 'updated_plan' keys.\"\"\"\n",
        "        )\n",
        "        # Set provider and model manually after initialization\n",
        "        chat.provider = \"groq\"\n",
        "        chat.model = \"llama3-70b-8192\"\n",
    ]
    
    # Apply the changes
    if init_start > 0 and init_end > init_start:
        content[init_start:init_end] = new_init
    
    if chat_init_start > 0 and chat_init_end > chat_init_start:
        content[chat_init_start:chat_init_end] = new_chat_init
    
    # Write the modified content back to the file
    with open('/app/backend/server.py', 'w') as f:
        f.writelines(content)
    
    print("Server.py has been fixed.")

if __name__ == "__main__":
    fix_server_py()
