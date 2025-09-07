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
    
    async def claim_conversation(self, conversation_id: int, agent_id: str, force: bool = False) -> dict:
        """
        Claim a conversation for an agent before sending messages
        Required to avoid EndUserNotFound errors
        """
        try:
            logger.info("🔒 DIXA SERVICE - Claiming conversation for agent")
            logger.info(f"   Conversation ID: {conversation_id}")
            logger.info(f"   Agent ID: {agent_id}")
            logger.info(f"   Force claim: {force}")
            
            url = f"{self.base_url}/conversations/{conversation_id}/claim"
            payload = {
                "agentId": agent_id,
                "force": force
            }
            
            logger.info(f"   Full URL: {url}")
            logger.info("   Making HTTP POST request...")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload
                )
                
                logger.info(f"   ✅ HTTP Response received: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info(f"   ✅ Successfully claimed conversation {conversation_id}")
                    return {
                        "success": True,
                        "status_code": response.status_code
                    }
                else:
                    logger.error(f"   ❌ Claim conversation error: {response.status_code}")
                    logger.error(f"   Response text: {response.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            logger.error(f"   ❌ Exception claiming conversation: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def send_message(self, conversation_id: int, dixa_payload: dict) -> dict:
        """
        Send message to Dixa conversation
        Matches exact HTTP POST from n8n "Send Email with webhook included" node
        """
        try:
            logger.info("📤 DIXA SERVICE - Sending message to conversation")
            logger.info(f"   Conversation ID: {conversation_id}")
            logger.info(f"   Base URL: {self.base_url}")
            logger.info(f"   Agent ID: {dixa_payload.get('agentId', 'Not specified')}")
            logger.info(f"   Content Type: {dixa_payload.get('content', {}).get('contentType', 'Unknown')}")
            logger.info(f"   Message Type: {dixa_payload.get('_type', 'Unknown')}")
            
            url = f"{self.base_url}/conversations/{conversation_id}/messages"
            logger.info(f"   Full URL: {url}")
            
            # Log payload structure (without full content for brevity)
            content_preview = dixa_payload.get('content', {}).get('value', '')[:200]
            logger.info(f"   Content preview: {content_preview}{'...' if len(content_preview) >= 200 else ''}")
            logger.info(f"   Payload size: {len(str(dixa_payload))} chars")
            
            logger.info("   Making HTTP POST request...")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=dixa_payload
                )
                
                logger.info(f"   ✅ HTTP Response received: {response.status_code}")
                logger.info(f"   Response headers: {dict(response.headers)}")
                
                if response.status_code == 200 or response.status_code == 201:
                    response_data = response.json() if response.content else {}
                    logger.info(f"   ✅ Message sent successfully to conversation {conversation_id}")
                    logger.info(f"   Response data keys: {list(response_data.keys()) if response_data else 'Empty response'}")
                    return {
                        "success": True,
                        "response": response_data,
                        "status_code": response.status_code
                    }
                else:
                    logger.error(f"   ❌ Dixa API error: {response.status_code}")
                    logger.error(f"   Response text: {response.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            logger.error(f"   ❌ Exception sending message to Dixa: {type(e).__name__}: {str(e)}")
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
            logger.info("🔄 DIXA SERVICE - Transferring conversation to queue")
            logger.info(f"   Conversation ID: {conversation_id}")
            logger.info(f"   User ID: {user_id}")
            logger.info(f"   Queue ID: {settings.QUEUE_ID}")
            logger.info(f"   Base URL: {self.base_url}")
            
            url = f"{self.base_url}/conversations/{conversation_id}/transfer/queue"
            logger.info(f"   Full URL: {url}")
            
            payload = {
                "queueId": settings.QUEUE_ID,
                "userId": user_id
            }
            
            logger.info(f"   Transfer payload: {payload}")
            logger.info("   Making HTTP PUT request...")
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    url,
                    headers=self.headers,
                    json=payload
                )
                
                logger.info(f"   ✅ HTTP Response received: {response.status_code}")
                logger.info(f"   Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    response_data = response.json() if response.content else {}
                    logger.info(f"   ✅ Successfully transferred conversation {conversation_id} to queue")
                    logger.info(f"   Response data: {response_data}")
                    return {
                        "success": True,
                        "response": response_data,
                        "status_code": response.status_code
                    }
                else:
                    logger.error(f"   ❌ Queue transfer error: {response.status_code}")
                    logger.error(f"   Response text: {response.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            logger.error(f"   ❌ Exception transferring to queue: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }