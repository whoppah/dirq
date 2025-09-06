from fastapi import APIRouter, HTTPException, Request
from models import WebhookPayload
from services import OpenAIService, MessageFormatter, DixaAPIService, MongoDBService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
openai_service = OpenAIService()
message_formatter = MessageFormatter()
dixa_service = DixaAPIService()
mongodb_service = MongoDBService()

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
                # Send message to Dixa (matching n8n "Send Email with webhook included" node)
                dixa_result = await dixa_service.send_message(
                    payload.data.conversation.csid,
                    formatted_response["dixa_payload"]
                )
                
                if dixa_result["success"]:
                    # Log to MongoDB (matching n8n Postgres node)
                    log_data = {
                        "conversation_id": payload.data.conversation.csid,
                        "message_id": payload.data.message_id,
                        "user_id": payload.data.author.id,
                        "ai_response": ai_response,
                        "is_initial_message": is_initial_message,
                        "time_diff_ms": time_diff,
                        "dixa_message_sent": True,
                        "original_text": payload.data.text
                    }
                    
                    log_result = await mongodb_service.log_conversation(log_data)
                    
                    return {
                        "status": "processed_and_sent",
                        "conversation_id": payload.data.conversation.csid,
                        "message_id": payload.data.message_id,
                        "isInitialMessage": is_initial_message,
                        "ai_response": ai_response,
                        "dixa_response": dixa_result["response"],
                        "message_sent": True,
                        "logged_to_db": log_result["success"]
                    }
                else:
                    # If sending fails, still return the processed response
                    logger.error(f"Failed to send message to Dixa: {dixa_result['error']}")
                    return {
                        "status": "processed_but_not_sent",
                        "conversation_id": payload.data.conversation.csid,
                        "message_id": payload.data.message_id,
                        "isInitialMessage": is_initial_message,
                        "ai_response": ai_response,
                        "dixa_error": dixa_result["error"],
                        "message_sent": False
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
async def response_webhook_no(user_id: str = None, conversation_id: int = None):
    """
    Webhook endpoint for handling "No" responses
    Matches the n8n "Webhook for Response No" node and triggers queue transfer
    """
    logger.info("Received 'No' response webhook")
    
    # Validate required parameters - no hardcoded values
    if not conversation_id:
        raise HTTPException(
            status_code=400, 
            detail="Missing required parameter: conversation_id"
        )
    
    if not user_id:
        raise HTTPException(
            status_code=400, 
            detail="Missing required parameter: user_id"
        )
    
    # Transfer to queue (matching n8n "Transfer Queue" node)
    transfer_result = await dixa_service.transfer_to_queue(conversation_id, user_id)
    
    if transfer_result["success"]:
        return {
            "status": "response_received_and_transferred",
            "action": "no",
            "conversation_id": conversation_id,
            "transferred_to_queue": True,
            "queue_id": transfer_result.get("response", {}).get("queueId", "unknown")
        }
    else:
        logger.error(f"Failed to transfer to queue: {transfer_result['error']}")
        return {
            "status": "response_received_but_transfer_failed",
            "action": "no",
            "conversation_id": conversation_id,
            "transferred_to_queue": False,
            "error": transfer_result["error"]
        }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "dixa-webhook"}