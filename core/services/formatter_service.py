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
        Format AI response as plain text (no HTML)
        Returns the exact payload structure for Dixa API
        """
        try:
            logger.info("🎨 FORMATTER SERVICE - Formatting response as plain text")
            logger.info(f"   AI Response length: {len(ai_response)} chars")
            logger.info(f"   AI Response preview: {ai_response[:150]}{'...' if len(ai_response) > 150 else ''}")

            # Just use plain text - no HTML formatting
            logger.info("   Using plain text format (no HTML)...")
            cleaned_response = self.clean_text_for_json(ai_response)
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