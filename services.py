import re
import json
import httpx
from openai import AsyncOpenAI
from pymongo import MongoClient
import logging
from datetime import datetime
from config import settings

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
                    "_type": "Html",
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

class DixaAPIService:
    """
    Service for interacting with Dixa API
    Implements exact HTTP requests from n8n workflow
    """
    
    def __init__(self):
        self.base_url = settings.DIXA_BASE_URL
        self.api_key = settings.DIXA_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def send_message(self, conversation_id: int, dixa_payload: dict) -> dict:
        """
        Send message to Dixa conversation
        Matches exact HTTP POST from n8n "Send Email with webhook included" node
        """
        try:
            url = f"{self.base_url}/conversations/{conversation_id}/messages"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=dixa_payload
                )
                
                if response.status_code == 200 or response.status_code == 201:
                    logger.info(f"Successfully sent message to conversation {conversation_id}")
                    return {
                        "success": True,
                        "response": response.json(),
                        "status_code": response.status_code
                    }
                else:
                    logger.error(f"Dixa API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            logger.error(f"Error sending message to Dixa: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def transfer_to_queue(self, conversation_id: int, user_id: str) -> dict:
        """
        Transfer conversation to queue
        Matches exact HTTP PUT from n8n "Transfer Queue" node
        """
        try:
            url = f"{self.base_url}/conversations/{conversation_id}/transfer/queue"
            
            payload = {
                "queueId": settings.QUEUE_ID,
                "userId": user_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    url,
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully transferred conversation {conversation_id} to queue")
                    return {
                        "success": True,
                        "response": response.json() if response.content else {},
                        "status_code": response.status_code
                    }
                else:
                    logger.error(f"Queue transfer error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            logger.error(f"Error transferring to queue: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

class MongoDBService:
    """
    Service for MongoDB operations
    Minimal implementation for conversation logging as per n8n Postgres node
    """
    
    def __init__(self):
        try:
            self.client = MongoClient(settings.MONGODB_URL)
            self.db = self.client.get_default_database()
            self.conversations_collection = self.db.conversations
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
    
    async def log_conversation(self, conversation_data: dict) -> dict:
        """
        Log conversation data to MongoDB
        Minimal implementation matching n8n Postgres node functionality
        """
        try:
            if not self.client:
                return {"success": False, "error": "MongoDB not connected"}
            
            # Add timestamp
            conversation_data["logged_at"] = datetime.utcnow()
            
            # Insert the document
            result = self.conversations_collection.insert_one(conversation_data)
            
            logger.info(f"Logged conversation {conversation_data.get('conversation_id')} to MongoDB")
            return {
                "success": True,
                "inserted_id": str(result.inserted_id)
            }
            
        except Exception as e:
            logger.error(f"Error logging to MongoDB: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }