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