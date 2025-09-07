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
<p><strong>Please confirm your response:</strong></p>
<div style="margin: 15px 0;">
<table cellpadding="0" cellspacing="0" border="0">
<tr>
<td style="padding-right: 10px;">
<a href="{base_url}/respond?answer=yes" 
   style="display: inline-block; padding: 12px 24px; background-color: #28a745; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: bold; border: 2px solid #28a745;">
✅ Yes
</a>
</td>
<td>
<a href="{base_url}/responded_false" 
   style="display: inline-block; padding: 12px 24px; background-color: #dc3545; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: bold; border: 2px solid #dc3545;">
❌ No
</a>
</td>
</tr>
</table>
</div>
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
    
    def format_response_with_webhook(self, ai_response: str, user_id: str = None, conversation_id: int = None) -> dict:
        """
        Format AI response with webhook buttons
        Returns the exact payload structure for Dixa API
        """
        try:
            logger.info("🎨 FORMATTER SERVICE - Formatting response with webhook buttons")
            logger.info(f"   AI Response length: {len(ai_response)} chars")
            logger.info(f"   AI Response preview: {ai_response[:150]}{'...' if len(ai_response) > 150 else ''}")
            logger.info(f"   Webhook base URL: {settings.WEBHOOK_BASE_URL}")
            
            # Generate dynamic webhook buttons with correct parameters
            logger.info("   Generating dynamic webhook buttons...")
            if user_id and conversation_id:
                webhook_content = f"""
<p><strong>Please confirm your response:</strong></p>
<div style="margin: 15px 0;">
<table cellpadding="0" cellspacing="0" border="0">
<tr>
<td style="padding-right: 10px;">
<a href="{settings.WEBHOOK_BASE_URL}/respond?answer=yes&user_id={user_id}&conversation_id={conversation_id}" 
   style="display: inline-block; padding: 12px 24px; background-color: #28a745; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: bold; border: 2px solid #28a745;">
✅ Yes
</a>
</td>
<td>
<a href="{settings.WEBHOOK_BASE_URL}/responded_false?user_id={user_id}&conversation_id={conversation_id}" 
   style="display: inline-block; padding: 12px 24px; background-color: #dc3545; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: bold; border: 2px solid #dc3545;">
❌ No
</a>
</td>
</tr>
</table>
</div>
"""
                logger.info(f"   Using dynamic parameters: user_id={user_id}, conversation_id={conversation_id}")
            else:
                webhook_content = self.webhook_content
                logger.info("   Using static webhook buttons (missing parameters)")
            
            # Append webhook buttons to the response
            logger.info("   Combining AI response with webhook buttons...")
            combined_content = ai_response + "\n\n" + webhook_content
            logger.info(f"   Combined content length: {len(combined_content)} chars")
            
            logger.info("   Cleaning text for JSON compatibility...")
            cleaned_response = self.clean_text_for_json(combined_content)
            logger.info(f"   Cleaned response length: {len(cleaned_response)} chars")
            
            # Prepare Dixa API payload - don't include userId for outbound agent messages
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
            
            logger.info("   Outbound message from agent - no userId needed")
            
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