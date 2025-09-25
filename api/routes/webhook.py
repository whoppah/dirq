from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
import logging
import json

from models.webhook import WebhookPayload
from api.dependencies import services
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/dixa_conversation_started")
async def dixa_webhook(payload: WebhookPayload):
    """
    Main webhook endpoint that receives Dixa conversation messages
    Replicates the exact functionality from n8n workflow
    """
    try:
        # Log incoming webhook details
        logger.info("=" * 80)
        logger.info("🔔 WEBHOOK RECEIVED - Dixa Conversation Started")
        logger.info(f"📞 Conversation ID: {payload.data.conversation.csid}")
        logger.info(f"📧 Author Email: {payload.data.author.email}")
        logger.info(f"👤 Author ID: {payload.data.author.id}")
        logger.info(f"💬 Message ID: {payload.data.message_id}")
        logger.info(f"📝 Message Text: {payload.data.text[:100]}{'...' if len(payload.data.text) > 100 else ''}")
        logger.info("=" * 80)
        
        # Idempotency: acquire reservation to avoid concurrent duplicates (use event_id)
        reservation_acquired = await services.mongodb_service.try_reserve_message(payload.event_id)
        if not reservation_acquired:
            logger.info("🛑 DUPLICATE WEBHOOK - Reservation not acquired (already processing), skipping")
            return {
                "status": "duplicate_ignored",
                "conversation_id": payload.data.conversation.csid,
                "message_id": payload.data.message_id,
                "event_id": payload.event_id,
                "reason": "Another worker is already processing this event"
            }

        # If we previously processed and sent, skip (release reservation)
        already_sent = await services.mongodb_service.has_event_been_processed(payload.event_id)
        if already_sent:
            logger.info("🛑 DUPLICATE WEBHOOK - Message already processed and sent, skipping")
            await services.mongodb_service.release_reservation(payload.event_id)
            return {
                "status": "duplicate_ignored",
                "conversation_id": payload.data.conversation.csid,
                "message_id": payload.data.message_id,
                "event_id": payload.event_id,
                "reason": "Message already processed and sent"
            }

        # Extract timestamps exactly as in n8n Python code
        conversation_created = payload.data.conversation.created_at
        message_created = payload.data.created_at
        
        logger.info("⏰ TIMESTAMP PROCESSING:")
        logger.info(f"   Conversation Created: {conversation_created}")
        logger.info(f"   Message Created: {message_created}")
        
        # Convert to datetime objects (matching n8n logic)
        conv_time = datetime.fromisoformat(conversation_created.replace('Z', '+00:00'))
        msg_time = datetime.fromisoformat(message_created.replace('Z', '+00:00'))
        
        # Calculate time difference in milliseconds (exact n8n logic)
        time_diff = (msg_time - conv_time).total_seconds() * 1000
        is_initial_message = time_diff <= 5000
        
        logger.info(f"   Time Difference: {time_diff}ms")
        logger.info(f"   Is Initial Message: {is_initial_message} (threshold: ≤5000ms)")
        
        # Domain validation - only process messages from whoppah.com domain
        author_email = payload.data.author.email
        logger.info("🔍 VALIDATION PROCESSING:")
        logger.info(f"   Checking email domain: {author_email}")
        
        should_process, validation_reason = services.validation_service.should_process_message(
            author_email, is_initial_message
        )
        
        logger.info(f"   Validation Result: {'✅ PASS' if should_process else '❌ FAIL'}")
        logger.info(f"   Validation Reason: {validation_reason}")
        
        # Conditional processing - only process if domain and initial message validation passes
        if should_process:
            logger.info("🤖 AI PROCESSING STARTED:")
            logger.info(f"   Processing message: '{payload.data.text}'")
            
            # First claim the conversation for the agent
            logger.info("🔒 CLAIMING CONVERSATION:")
            logger.info(f"   Claiming conversation {payload.data.conversation.csid} for agent {settings.AGENT_ID}")
            
            claim_result = await services.dixa_service.claim_conversation(
                payload.data.conversation.csid,
                settings.AGENT_ID,
                force=False  # Don't force to avoid taking over assigned conversations
            )
            
            if not claim_result["success"]:
                logger.error(f"   ❌ Failed to claim conversation: {claim_result.get('error', 'Unknown error')}")
                # Continue anyway - conversation might already be claimed
                logger.info("   Continuing with message processing despite claim failure...")
            else:
                logger.info("   ✅ Conversation claimed successfully")
            
            # Process with OpenAI Prompts (using customer name from payload)
            logger.info("🤖 AI PROCESSING:")
            logger.info("   Calling OpenAI service...")
            try:
                # Extract customer name from payload
                customer_name = payload.data.author.name
                logger.info(f"   Customer name extracted: {customer_name}")
                
                ai_response = await services.openai_service.process_message(
                    payload.data.text, 
                    customer_name=customer_name
                )
                logger.info(f"   ✅ OpenAI Response received: {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}")
            except Exception as openai_error:
                logger.error(f"   ❌ OpenAI service failed: {type(openai_error).__name__}: {str(openai_error)}")
                ai_response = f"Error: OpenAI service failed - {str(openai_error)}"
            
            # Format response with webhook buttons (matching n8n Json converter node)
            logger.info("   Formatting response with webhook buttons...")
            formatted_response = services.message_formatter.format_response_with_webhook(
                ai_response, 
                user_id=payload.data.author.id,
                conversation_id=payload.data.conversation.csid
            )
            logger.info(f"   ✅ Response formatted successfully: {formatted_response.get('success', False)}")
            
            if formatted_response["success"]:
                # Send message to Dixa (matching n8n "Send Email with webhook included" node)
                logger.info("📤 DIXA MESSAGE SENDING:")
                logger.info(f"   Sending to conversation: {payload.data.conversation.csid}")
                logger.info(f"   Payload size: {len(str(formatted_response['dixa_payload']))} chars")
                
                dixa_result = await services.dixa_service.send_message(
                    payload.data.conversation.csid,
                    formatted_response["dixa_payload"]
                )
                
                logger.info(f"   ✅ Dixa send result: {dixa_result.get('success', False)}")
                if not dixa_result.get('success'):
                    logger.error(f"   ❌ Dixa error: {dixa_result.get('error', 'Unknown error')}")
                
                if dixa_result["success"]:
                    # Log to MongoDB (matching n8n Postgres node)
                    logger.info("💾 DATABASE LOGGING:")
                    log_data = {
                        "conversation_id": payload.data.conversation.csid,
                        "message_id": payload.data.message_id,
                        "event_id": payload.event_id,
                        "user_id": payload.data.author.id,
                        "ai_response": ai_response,
                        "is_initial_message": is_initial_message,
                        "time_diff_ms": time_diff,
                        "dixa_message_sent": True,
                        "original_text": payload.data.text
                    }
                    
                    logger.info(f"   Logging conversation data to MongoDB...")
                    log_result = await services.mongodb_service.log_conversation(log_data)
                    logger.info(f"   ✅ Database log result: {log_result.get('success', False)}")
                    if not log_result.get('success'):
                        logger.error(f"   ❌ Database error: {log_result.get('error', 'Unknown error')}")
                    
                    logger.info("🎉 WEBHOOK PROCESSING COMPLETED SUCCESSFULLY!")
                    logger.info("=" * 80)
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
                    logger.error("❌ DIXA SEND FAILED - Processing completed but message not sent")
                    logger.error(f"   Error: {dixa_result['error']}")
                    # Release idempotency reservation on failure to allow retry
                    await services.mongodb_service.release_reservation(payload.event_id)
                    logger.info("=" * 80)
                    return {
                        "status": "processed_but_not_sent",
                        "conversation_id": payload.data.conversation.csid,
                        "message_id": payload.data.message_id,
                        "event_id": payload.event_id,
                        "isInitialMessage": is_initial_message,
                        "ai_response": ai_response,
                        "dixa_error": dixa_result["error"],
                        "message_sent": False
                    }
            else:
                logger.error("❌ RESPONSE FORMATTING FAILED")
                logger.error(f"   Error: {formatted_response.get('error', 'Unknown formatting error')}")
                # Release idempotency reservation on error
                await services.mongodb_service.release_reservation(payload.event_id)
                logger.info("=" * 80)
                raise HTTPException(status_code=500, detail=f"Error formatting response: {formatted_response['error']}")
        else:
            # No operation for messages that don't meet validation criteria
            logger.info("⏭️  MESSAGE SKIPPED:")
            logger.info(f"   Reason: {validation_reason}")
            logger.info(f"   Email: {author_email}")
            logger.info(f"   Initial Message: {is_initial_message}")
            logger.info("=" * 80)
            # Release reservation since we're not processing/sending
            await services.mongodb_service.release_reservation(payload.event_id)
            return {
                "status": "ignored",
                "conversation_id": payload.data.conversation.csid,
                "message_id": payload.data.message_id,
                "event_id": payload.event_id,
                "author_email": author_email,
                "isInitialMessage": is_initial_message,
                "validation_reason": validation_reason,
                "reason": "Validation failed or not an initial message"
            }
        
    except Exception as e:
        logger.error("💥 WEBHOOK ERROR - Unexpected exception occurred")
        logger.error(f"   Exception Type: {type(e).__name__}")
        logger.error(f"   Exception Message: {str(e)}")
        # Safely access payload attributes only if payload exists
        if 'payload' in locals() and hasattr(payload, 'data') and hasattr(payload.data, 'conversation'):
            logger.error(f"   Conversation ID: {getattr(payload.data.conversation, 'csid', 'Unknown')}")
        else:
            logger.error("   Conversation ID: Unknown (payload not available)")
        logger.error("=" * 80)
        # Best-effort release of reservation on unexpected exceptions
        try:
            if 'payload' in locals() and hasattr(payload, 'event_id'):
                await services.mongodb_service.release_reservation(payload.event_id)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")

@router.get("/responded_false")
async def response_webhook_no(user_id: str = None, conversation_id: int = None):
    """
    Webhook endpoint for handling "No" responses
    Matches the n8n "Webhook for Response No" node and triggers queue transfer
    """
    logger.info("=" * 80)
    logger.info("🔔 WEBHOOK RECEIVED - Response 'No' Endpoint")
    logger.info(f"👤 User ID: {user_id}")
    logger.info(f"📞 Conversation ID: {conversation_id}")
    
    # Validate required parameters - no hardcoded values
    if not conversation_id:
        logger.error("❌ VALIDATION ERROR: conversation_id is required")
        raise HTTPException(
            status_code=400, 
            detail="Missing required parameter: conversation_id"
        )
    
    if not user_id:
        logger.error("❌ VALIDATION ERROR: user_id is required")
        raise HTTPException(
            status_code=400, 
            detail="Missing required parameter: user_id"
        )
    
    # Transfer to queue (matching n8n "Transfer Queue" node)
    logger.info("🔄 QUEUE TRANSFER PROCESSING:")
    logger.info(f"   Transferring conversation {conversation_id} to queue...")
    logger.info(f"   User ID: {user_id}")
    
    transfer_result = await services.dixa_service.transfer_to_queue(conversation_id, user_id)
    
    if transfer_result["success"]:
        logger.info("✅ QUEUE TRANSFER SUCCESSFUL!")
        logger.info(f"   Queue ID: {transfer_result.get('response', {}).get('queueId', 'unknown')}")
        logger.info("=" * 80)
        return {
            "status": "response_received_and_transferred",
            "action": "no",
            "conversation_id": conversation_id,
            "transferred_to_queue": True,
            "queue_id": transfer_result.get("response", {}).get("queueId", "unknown")
        }
    else:
        logger.error("❌ QUEUE TRANSFER FAILED!")
        logger.error(f"   Error: {transfer_result['error']}")
        logger.error("=" * 80)
        return {
            "status": "response_received_but_transfer_failed",
            "action": "no",
            "conversation_id": conversation_id,
            "transferred_to_queue": False,
            "error": transfer_result["error"]
        }