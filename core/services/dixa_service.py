import httpx
import logging
from config import settings

logger = logging.getLogger(__name__)

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