import re
import json
from openai import AsyncOpenAI
from config import settings
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.assistant_id = settings.OPENAI_ASSISTANT_ID
    
    async def process_message(self, user_text: str) -> str:
        """
        Process user message using OpenAI Assistant API
        Matches the exact OpenAI node configuration from n8n
        """
        try:
            # Create a thread
            thread = await self.client.beta.threads.create()
            
            # Add the user message to the thread
            await self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Users email:\n {user_text}"  # Exact format from n8n
            )
            
            # Run the assistant
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Wait for completion
            while run.status in ["queued", "in_progress"]:
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                # Get the assistant's response
                messages = await self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                
                # Get the latest assistant message
                for message in messages.data:
                    if message.role == "assistant":
                        return message.content[0].text.value
                        
            logger.error(f"OpenAI run failed with status: {run.status}")
            return "Error: Could not generate response"
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return f"Error: {str(e)}"

class MessageFormatter:
    """
    Formats AI responses with webhook buttons
    Implements exact logic from n8n "Json converter + webhook" node
    """
    
    def __init__(self):
        self.webhook_content = """
<p>Please confirm your response:</p>

<a href="https://your-webhook-url.com/respond?answer=yes"
   style="display: inline-block; padding: 10px 20px; margin-right: 10px; background-color: #28a745; color: white; text-decoration: none; border-radius: 4px;">
   Yes
</a>

<a href="https://your-webhook-url.com/responded_false"
   style="display: inline-block; padding: 10px 20px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 4px;">
   No
</a>
"""
    
    def clean_text_for_json(self, text: str) -> str:
        """
        Clean text to be safely used in JSON
        Exact implementation from n8n Python code
        """
        if not text:
            return ""

        # Normalize line breaks and whitespace
        cleaned = text.replace('\r\n', '\n').replace('\r', '\n')
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = cleaned.strip()

        return cleaned
    
    def format_response_with_webhook(self, ai_response: str) -> dict:
        """
        Format AI response with webhook buttons
        Returns the exact payload structure for Dixa API
        """
        try:
            # Append webhook buttons to the response
            combined_content = ai_response + "\n\n" + self.webhook_content
            cleaned_response = self.clean_text_for_json(combined_content)
            
            # Prepare Dixa API payload (exact structure from n8n)
            payload = {
                "agentId": settings.AGENT_ID,
                "content": {
                    "_type": "Text",
                    "value": cleaned_response,
                    "contentType": "text/html"
                },
                "_type": "Outbound"
            }
            
            return {
                "cleaned_response": cleaned_response,
                "dixa_payload": payload,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }