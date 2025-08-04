from fastapi import APIRouter, HTTPException, Request
from models import WebhookPayload
from services import OpenAIService, MessageFormatter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
openai_service = OpenAIService()
message_formatter = MessageFormatter()

@router.post("/dixa_conversation_started")
async def dixa_webhook(payload: WebhookPayload):
    """
    Main webhook endpoint that receives Dixa conversation messages
    Replicates the exact functionality from n8n workflow
    """
    try:
        logger.info(f"Received webhook for conversation {payload.data.conversation.csid}")
        
        # Extract timestamps exactly as in n8n Python code
        conversation_created = payload.data.conversation.created_at
        message_created = payload.data.created_at
        
        # Convert to datetime objects (matching n8n logic)
        conv_time = datetime.fromisoformat(conversation_created.replace('Z', '+00:00'))
        msg_time = datetime.fromisoformat(message_created.replace('Z', '+00:00'))
        
        # Calculate time difference in milliseconds (exact n8n logic)
        time_diff = (msg_time - conv_time).total_seconds() * 1000
        is_initial_message = time_diff <= 5000
        
        logger.info(f"Time difference: {time_diff}ms, Initial message: {is_initial_message}")
        
        # Conditional processing - only process initial messages (matching n8n If node)
        if is_initial_message:
            logger.info("Processing initial message with OpenAI")
            
            # Process with OpenAI Assistant (matching n8n OpenAI node)
            ai_response = await openai_service.process_message(payload.data.text)
            
            # Format response with webhook buttons (matching n8n Json converter node)
            formatted_response = message_formatter.format_response_with_webhook(ai_response)
            
            if formatted_response["success"]:
                return {
                    "status": "processed",
                    "conversation_id": payload.data.conversation.csid,
                    "message_id": payload.data.message_id,
                    "isInitialMessage": is_initial_message,
                    "ai_response": ai_response,
                    "formatted_response": formatted_response["cleaned_response"],
                    "dixa_payload": formatted_response["dixa_payload"]
                }
            else:
                raise HTTPException(status_code=500, detail=f"Error formatting response: {formatted_response['error']}")
        else:
            # No operation for non-initial messages (matching n8n "No Operation" node)
            logger.info("Non-initial message - no processing required")
            return {
                "status": "ignored",
                "conversation_id": payload.data.conversation.csid,
                "message_id": payload.data.message_id,
                "isInitialMessage": is_initial_message,
                "reason": "Not an initial message"
            }
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")

@router.get("/responded_false")
async def response_webhook_no():
    """
    Webhook endpoint for handling "No" responses
    Matches the n8n "Webhook for Response No" node
    """
    logger.info("Received 'No' response webhook")
    return {"status": "response_received", "action": "no"}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "dixa-webhook"}