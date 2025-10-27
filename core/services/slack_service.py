import logging
from typing import Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import settings

logger = logging.getLogger(__name__)

class SlackService:
    """
    Service for sending notifications to Slack channels
    """
    
    def __init__(self):
        self.client = WebClient(token=settings.SLACK_BOT_TOKEN)
        self.channel_id = settings.SLACK_CHANNEL_ID
    
    async def send_notification(
        self,
        user_email: str,
        user_message: str,
        ai_response: str,
        conversation_id: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a notification to Slack with user email and AI response
        
        Args:
            user_email: Email of the user who sent the message
            user_message: Original message from the user
            ai_response: AI-generated response
            conversation_id: Dixa conversation ID
            additional_context: Optional additional context to include
            
        Returns:
            Dict with success status and response/error
        """
        try:
            if not self.client.token:
                logger.error("Slack bot token not configured")
                return {
                    "success": False,
                    "error": "Slack bot token not configured"
                }
            
            if not self.channel_id:
                logger.error("Slack channel ID not configured")
                return {
                    "success": False,
                    "error": "Slack channel ID not configured"
                }
            
            # Build the Slack message payload
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🤖 AI Response Generated",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*User Email:*\n{user_email}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Conversation ID:*\n{conversation_id}"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*User Message:*\n```{user_message[:500]}{'...' if len(user_message) > 500 else ''}```"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*AI Response:*\n```{ai_response[:1000]}{'...' if len(ai_response) > 1000 else ''}```"
                    }
                }
            ]
            
            # Add additional context if provided
            if additional_context:
                context_text = "\n".join([f"*{k}:* {v}" for k, v in additional_context.items()])
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Additional Context:*\n{context_text}"
                    }
                })
            
            logger.info(f"Sending Slack notification for conversation {conversation_id}")
            
            # Send message using Slack SDK
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                blocks=blocks,
                text=f"AI Response for {user_email}"  # Fallback text for notifications
            )
            
            if response["ok"]:
                logger.info(f"✅ Slack notification sent successfully for {user_email}")
                return {
                    "success": True,
                    "response": response
                }
            else:
                logger.error(f"❌ Slack API error: {response}")
                return {
                    "success": False,
                    "error": f"Slack API returned error: {response}"
                }
                    
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {
                "success": False,
                "error": f"Slack API error: {e.response['error']}"
            }
        except Exception as e:
            logger.error(f"Error sending Slack notification: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "error": f"Slack error: {str(e)}"
            }
