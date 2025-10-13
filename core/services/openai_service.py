import logging
import json
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
        )
        self.prompt_id = settings.OPENAI_PROMPT_ID
    
    async def process_message(self, user_text: str, customer_name: str = None, conversation_id: int = None, user_context: str = None) -> dict:
        """
        Process user message using OpenAI Prompts API
        Uses prompt templates with email, customer_first_name, and user_context variables
        Note: conversation_id parameter accepted but not used (prompt doesn't support it)
        """
        try:
            logger.info("🤖 OPENAI SERVICE - Starting message processing with prompts")
            logger.info(f"   Prompt ID: {self.prompt_id}")
            logger.info(f"   Customer Name: {customer_name}")
            logger.info(f"   Conversation ID: {conversation_id}")
            logger.info(f"   Has User Context: {bool(user_context)}")
            logger.info(f"   Input text length: {len(user_text)} chars")
            logger.info(f"   Input preview: {user_text[:100]}{'...' if len(user_text) > 100 else ''}")

            # Prepare prompt variables
            prompt_variables = {
                "email": user_text
            }

            # Add customer name if available
            if customer_name:
                prompt_variables["customer_first_name"] = customer_name
                logger.info(f"   Added customer_first_name variable: {customer_name}")

            # Add user context if available (only if prompt supports it)
            # NOTE: If you get "Missing prompt variables: user_context" error,
            # you need to add user_context as a variable in your OpenAI prompt first
            if user_context:
                prompt_variables["user_context"] = user_context
                logger.info(f"   Added user_context variable ({len(user_context)} chars)")
            else:
                logger.info(f"   No user_context provided - prompt must handle missing user_context gracefully")

            logger.info(f"   Prompt variables: {list(prompt_variables.keys())}")

            # Call OpenAI Prompts API
            logger.info("   Calling OpenAI Prompts API...")
            response = await self.client.responses.create(
                prompt={
                    "id": self.prompt_id,
                    "version": "9",
                    "variables": prompt_variables
                }
            )
            
            logger.info("   ✅ OpenAI Prompts response received")
            
            # Extract response content (prefer the new Responses API output_text)
            ai_response = None
            if response and hasattr(response, "output_text") and response.output_text:
                ai_response = response.output_text
            elif response and hasattr(response, "content"):
                ai_response = response.content

            if not ai_response:
                logger.error("   ❌ No content in OpenAI response")
                return {
                    "email": "Error: No response content received from OpenAI",
                    "handoff": False
                }

            # Try to parse JSON response
            handoff_required = False
            email_content = ai_response

            try:
                parsed = json.loads(ai_response)
                if isinstance(parsed, dict):
                    # Extract email field
                    if "email" in parsed:
                        logger.info("   Detected JSON response with 'email' field")
                        email_content = parsed["email"]

                    # Check for handoff flag
                    if "handoff" in parsed:
                        handoff_required = parsed["handoff"]
                        logger.info(f"   Handoff flag detected: {handoff_required}")
                    else:
                        # Fallback: detect handoff from email content
                        handoff_required = self._detect_handoff_in_content(email_content)
                        logger.info(f"   Handoff detected from content: {handoff_required}")
            except json.JSONDecodeError:
                # Not JSON; keep the raw text and detect handoff from content
                logger.info("   Response is not JSON, using raw text")
                handoff_required = self._detect_handoff_in_content(email_content)
                logger.info(f"   Handoff detected from content: {handoff_required}")

            logger.info(f"   Response length: {len(email_content)} chars")
            logger.info(f"   Response preview: {email_content[:200]}{'...' if len(email_content) > 200 else ''}")

            return {
                "email": email_content,
                "handoff": handoff_required
            }
            
        except Exception as e:
            logger.error(f"   ❌ OpenAI Prompts API error: {type(e).__name__}: {str(e)}")
            return {
                "email": f"Error: {str(e)}",
                "handoff": False
            }

    def _detect_handoff_in_content(self, email_content: str) -> bool:
        """
        Fallback method to detect handoff from email content
        Looks for the standard handoff phrase
        """
        if not email_content:
            return False

        # Standard handoff phrase from prompt
        handoff_phrases = [
            "I'll connect you with a colleague who can help you better with this",
            "I'll connect you with a colleague",
            "connect you with a colleague",
            "colleague who can help you better"
        ]

        email_lower = email_content.lower()
        for phrase in handoff_phrases:
            if phrase.lower() in email_lower:
                return True

        return False