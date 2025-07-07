"""Chat service for Vercel serverless functions"""
import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
import litellm

logger = logging.getLogger(__name__)

class ChatService:
    """AI chat service for plan modifications"""
    
    def __init__(self):
        self.groq_api_key = os.environ.get('GROQ_API_KEY')
        self.system_message = """You are an AI assistant helping users modify video generation plans. 

You receive the current generation plan and user requests for modifications. Your job is to:
1. Understand what the user wants to change
2. Provide helpful suggestions and explanations
3. Update the generation plan if requested
4. Keep responses conversational and helpful

When updating plans, maintain the JSON structure and only modify relevant sections.
Always return your response in JSON format with 'response' and 'updated_plan' keys (updated_plan is optional)."""
    
    async def process_chat_message(self, message: str, current_plan: Optional[Dict[str, Any]] = None,
                                 chat_history: Optional[list] = None) -> Dict[str, Any]:
        """Process chat message and optionally update plan"""
        try:
            # Prepare context
            context_info = ""
            if current_plan:
                context_info = f"\n\nCurrent generation plan:\n{json.dumps(current_plan, indent=2)}"
            
            if chat_history and len(chat_history) > 0:
                recent_messages = chat_history[-6:]  # Last 3 exchanges
                context_info += f"\n\nRecent conversation:\n"
                for msg in recent_messages:
                    if isinstance(msg, dict):
                        if 'user_message' in msg:
                            context_info += f"User: {msg['user_message']}\n"
                        if 'ai_response' in msg:
                            context_info += f"AI: {msg['ai_response']}\n"
            
            # Create chat prompt
            chat_prompt = f"""
            User message: {message}
            {context_info}
            
            Please provide a helpful response about modifying the video generation plan.
            If the user wants to change something specific, provide updated plan suggestions.
            Keep your response conversational and focused on video generation.
            
            Return response in JSON format with 'response' and optionally 'updated_plan' keys.
            """
            
            # Use litellm for chat
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": chat_prompt}
            ]
            
            response = await asyncio.to_thread(
                litellm.completion,
                model="groq/llama3-8b-8192",
                messages=messages,
                api_key=self.groq_api_key,
                temperature=0.7,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                chat_data = json.loads(response_text)
                
                # Ensure proper structure
                if not isinstance(chat_data, dict):
                    chat_data = {"response": response_text}
                
                if "response" not in chat_data:
                    chat_data["response"] = response_text
                
                return chat_data
                
            except json.JSONDecodeError:
                # If not valid JSON, return as simple response
                return {
                    "response": response_text,
                    "note": "Response was not in JSON format"
                }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            return {
                "response": "I'm having trouble processing your message right now. Could you please try rephrasing your request?",
                "error": "Chat processing failed"
            }
    
    def add_message_to_history(self, chat_history: list, user_message: str, ai_response: str) -> list:
        """Add message exchange to chat history"""
        if not isinstance(chat_history, list):
            chat_history = []
        
        chat_entry = {
            "user_message": user_message,
            "ai_response": ai_response,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        chat_history.append(chat_entry)
        
        # Keep only last 20 exchanges to avoid bloat
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
        
        return chat_history

# Create global chat service instance
chat_service = ChatService()