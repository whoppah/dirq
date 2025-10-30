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
        logger.info(f"🆔 Event ID: {payload.event_id}")
        logger.info(f"📝 Message Text: {payload.data.text[:100]}{'...' if len(payload.data.text) > 100 else ''}")
        logger.info("=" * 80)

        # Step 1: Check if we already processed this event (fastest check)
        already_processed = await services.mongodb_service.has_event_been_processed(payload.event_id)
        if already_processed:
            logger.info("🛑 DUPLICATE WEBHOOK - Event already processed (found in conversations), skipping")
            return {
                "status": "duplicate_ignored",
                "conversation_id": payload.data.conversation.csid,
                "message_id": payload.data.message_id,
                "event_id": payload.event_id,
                "reason": "Event already processed (logged in database)"
            }

        # Step 2: Try to acquire reservation for this event (prevents concurrent processing)
        logger.info(f"🔐 Attempting to acquire reservation for event: {payload.event_id}")
        reservation_acquired = await services.mongodb_service.try_reserve_message(payload.event_id)

        if not reservation_acquired:
            logger.info("🛑 DUPLICATE WEBHOOK - Reservation not acquired (concurrent request), skipping")

            # Check if MongoDB is connected
            if not services.mongodb_service.client:
                logger.error("❌ MongoDB connection is DOWN - cannot process webhooks safely")
                raise HTTPException(
                    status_code=503,
                    detail="Service temporarily unavailable: Database connection required for idempotency"
                )

            return {
                "status": "duplicate_ignored",
                "conversation_id": payload.data.conversation.csid,
                "message_id": payload.data.message_id,
                "event_id": payload.event_id,
                "reason": "Another worker is already processing this event"
            }

        logger.info(f"✅ Reservation acquired successfully for event: {payload.event_id}")
        logger.info("📋 Starting webhook processing...")

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
            
            # Fetch user context from Dashboard API before OpenAI processing
            logger.info("📊 DASHBOARD API - Fetching user context")
            user_context_formatted = None

            # Only fetch if Dashboard API token is configured
            if settings.DASHBOARD_API_TOKEN:
                user_context_data = await services.dashboard_service.get_user_context(
                    email=payload.data.author.email,
                    orders_limit=10,
                    threads_limit=10
                )

                # Format user context for OpenAI if available
                if user_context_data:
                    user_context_formatted = services.dashboard_service.format_user_context(user_context_data)
                    logger.info(f"   ✅ User context formatted ({len(user_context_formatted)} chars)")
                else:
                    logger.info("   ⚠️  No user context available - proceeding without it")
            else:
                logger.info("   ⚠️  Dashboard API token not configured - skipping user context fetch")

            # Process with OpenAI Prompts (using customer name and user context from payload)
            logger.info("🤖 AI PROCESSING:")
            logger.info("   Calling OpenAI service...")
            try:
                # Extract customer name from payload (fallback to "customer" if null)
                customer_name = payload.data.author.name or "customer"
                logger.info(f"   Customer name extracted: {customer_name}")

                openai_result = await services.openai_service.process_message(
                    payload.data.text,
                    customer_name=customer_name,
                    conversation_id=payload.data.conversation.csid,
                    user_context=user_context_formatted
                )

                ai_response = openai_result.get("email", "")
                handoff_required = openai_result.get("handoff", False)

                logger.info(f"   ✅ OpenAI Response received: {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}")
                logger.info(f"   🔄 Handoff required: {handoff_required}")
            except Exception as openai_error:
                logger.error(f"   ❌ OpenAI service failed: {type(openai_error).__name__}: {str(openai_error)}")
                ai_response = f"Error: OpenAI service failed - {str(openai_error)}"
                handoff_required = False
            
            # Send Slack notification (always)
            logger.info("📤 SLACK NOTIFICATION SENDING:")
            logger.info(f"   User Email: {payload.data.author.email}")
            logger.info(f"   Conversation ID: {payload.data.conversation.csid}")
            
            slack_result = await services.slack_service.send_notification(
                user_email=payload.data.author.email,
                user_message=payload.data.text,
                ai_response=ai_response,
                conversation_id=payload.data.conversation.csid,
                additional_context={
                    "handoff_required": handoff_required,
                    "is_initial_message": is_initial_message
                }
            )
            
            logger.info(f"   ✅ Slack send result: {slack_result.get('success', False)}")
            if not slack_result.get('success'):
                logger.error(f"   ❌ Slack error: {slack_result.get('error', 'Unknown error')}")
            
            # Initialize dixa_result for tracking
            dixa_result = {"success": False, "skipped": False}
            
            # Only send Dixa reply if handoff is NOT required
            if not handoff_required:
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
                else:
                    logger.error("❌ RESPONSE FORMATTING FAILED")
                    logger.error(f"   Error: {formatted_response.get('error', 'Unknown formatting error')}")
            else:
                logger.info("⏭️  SKIPPING DIXA REPLY - Handoff required, will transfer to human agent")
                dixa_result = {"success": False, "skipped": True}
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
                "dixa_message_sent": dixa_result.get("success", False),
                "slack_notification_sent": slack_result.get("success", False),
                "original_text": payload.data.text,
                "handoff_required": handoff_required
            }
            
            logger.info(f"   Logging conversation data to MongoDB...")
            log_result = await services.mongodb_service.log_conversation(log_data)
            logger.info(f"   ✅ Database log result: {log_result.get('success', False)}")
            if not log_result.get('success'):
                logger.error(f"   ❌ Database error: {log_result.get('error', 'Unknown error')}")

            # Handle handoff to human agent if required
            if handoff_required:
                logger.info("🔄 HANDOFF REQUIRED - Transferring to queue")
                logger.info(f"   Transferring conversation {payload.data.conversation.csid} to queue...")
                
                transfer_result = await services.dixa_service.transfer_to_queue(
                    payload.data.conversation.csid,
                    settings.AGENT_ID  # Use agent ID instead of customer ID
                )
                
                if transfer_result["success"]:
                    logger.info(f"   ✅ Successfully transferred to queue")
                else:
                    logger.error(f"   ❌ Queue transfer failed: {transfer_result.get('error', 'Unknown error')}")

                logger.info("🎉 WEBHOOK PROCESSING COMPLETED WITH HANDOFF!")
                logger.info("=" * 80)
                return {
                    "status": "processed_with_handoff",
                    "conversation_id": payload.data.conversation.csid,
                    "message_id": payload.data.message_id,
                    "isInitialMessage": is_initial_message,
                    "ai_response": ai_response,
                    "slack_notification_sent": slack_result.get("success", False),
                    "dixa_message_sent": False,
                    "logged_to_db": log_result["success"],
                    "handoff_detected": True,
                    "transferred_to_queue": transfer_result.get("success", False)
                }

            logger.info("🎉 WEBHOOK PROCESSING COMPLETED SUCCESSFULLY!")
            logger.info("=" * 80)
            return {
                "status": "processed_and_sent",
                "conversation_id": payload.data.conversation.csid,
                "message_id": payload.data.message_id,
                "isInitialMessage": is_initial_message,
                "ai_response": ai_response,
                "slack_notification_sent": slack_result.get("success", False),
                "dixa_message_sent": dixa_result.get("success", False),
                "logged_to_db": log_result["success"],
                "handoff_detected": False
            }
        else:
            # No operation for messages that don't meet validation criteria
            logger.info("⏭️  MESSAGE SKIPPED:")
            logger.info(f"   Reason: {validation_reason}")
            logger.info(f"   Email: {author_email}")
            logger.info(f"   Initial Message: {is_initial_message}")

            # Log skipped message to prevent re-processing on duplicate webhooks
            logger.info("💾 DATABASE LOGGING (SKIPPED MESSAGE):")
            log_data = {
                "conversation_id": payload.data.conversation.csid,
                "message_id": payload.data.message_id,
                "event_id": payload.event_id,
                "user_id": payload.data.author.id,
                "ai_response": None,
                "is_initial_message": is_initial_message,
                "time_diff_ms": time_diff,
                "dixa_message_sent": False,
                "original_text": payload.data.text,
                "skipped_reason": validation_reason
            }

            log_result = await services.mongodb_service.log_conversation(log_data)
            logger.info(f"   ✅ Skipped message logged: {log_result.get('success', False)}")
            logger.info("=" * 80)

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
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 503 from MongoDB down)
        raise
    except Exception as e:
        logger.error("💥 WEBHOOK ERROR - Unexpected exception occurred")
        logger.error(f"   Exception Type: {type(e).__name__}")
        logger.error(f"   Exception Message: {str(e)}")
        # Log full stack trace for debugging
        import traceback
        logger.error(f"   Stack Trace:\n{traceback.format_exc()}")
        # Safely access payload attributes only if payload exists
        if 'payload' in locals() and hasattr(payload, 'data') and hasattr(payload.data, 'conversation'):
            logger.error(f"   Conversation ID: {getattr(payload.data.conversation, 'csid', 'Unknown')}")
            logger.error(f"   Event ID: {getattr(payload, 'event_id', 'Unknown')}")
        else:
            logger.error("   Payload info: Unknown (payload not available)")
        logger.error("=" * 80)
        # Best-effort release of reservation on unexpected exceptions
        try:
            if 'payload' in locals() and hasattr(payload, 'event_id'):
                logger.info(f"   Releasing reservation for event: {payload.event_id}")
                await services.mongodb_service.release_reservation(payload.event_id)
        except Exception as release_err:
            logger.error(f"   Failed to release reservation: {release_err}")
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