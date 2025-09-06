import re
import logging
from config import settings

logger = logging.getLogger(__name__)

class MessageFormatter:
    """
    Formats AI responses with webhook buttons
    Implements exact logic from n8n "Json converter + webhook" node
    """
    
    def __init__(self):
        # Fix webhook URLs to use actual base URL instead of placeholder
        base_url = settings.WEBHOOK_BASE_URL
        self.webhook_content = f"""
<p>Please confirm your response:</p>

<a href="{base_url}/respond?answer=yes"
   style="display: inline-block; padding: 10px 20px; margin-right: 10px; background-color: #28a745; color: white; text-decoration: none; border-radius: 4px;">
   Yes
</a>

<a href="{base_url}/responded_false"
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
            logger.info("🎨 FORMATTER SERVICE - Formatting response with webhook buttons")
            logger.info(f"   AI Response length: {len(ai_response)} chars")
            logger.info(f"   AI Response preview: {ai_response[:150]}{'...' if len(ai_response) > 150 else ''}")
            logger.info(f"   Webhook base URL: {settings.WEBHOOK_BASE_URL}")
            
            # Append webhook buttons to the response
            logger.info("   Combining AI response with webhook buttons...")
            combined_content = ai_response + "\n\n" + self.webhook_content
            logger.info(f"   Combined content length: {len(combined_content)} chars")
            
            logger.info("   Cleaning text for JSON compatibility...")
            cleaned_response = self.clean_text_for_json(combined_content)
            logger.info(f"   Cleaned response length: {len(cleaned_response)} chars")
            
            # Prepare Dixa API payload (exact structure from n8n)
            logger.info("   Building Dixa API payload...")
            payload = {
                "agentId": settings.AGENT_ID,
                "content": {
                    "_type": "Text",
                    "value": cleaned_response,
                    "contentType": "text/html"
                },
                "_type": "Outbound"
            }
            
            logger.info(f"   ✅ Payload created successfully:")
            logger.info(f"      Agent ID: {settings.AGENT_ID}")
            logger.info(f"      Content Type: text/html")
            logger.info(f"      Message Type: Outbound")
            logger.info(f"      Final payload size: {len(str(payload))} chars")
            
            return {
                "cleaned_response": cleaned_response,
                "dixa_payload": payload,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"   ❌ Error formatting response: {type(e).__name__}: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }