import logging
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
        )
        self.prompt_id = settings.OPENAI_PROMPT_ID
    
    async def process_message(self, user_text: str, customer_name: str = None) -> str:
        """
        Process user message using OpenAI Prompts API
        Uses prompt templates with customer name variable
        """
        try:
            logger.info("🤖 OPENAI SERVICE - Starting message processing with prompts")
            logger.info(f"   Prompt ID: {self.prompt_id}")
            logger.info(f"   Customer Name: {customer_name}")
            logger.info(f"   Input text length: {len(user_text)} chars")
            logger.info(f"   Input preview: {user_text[:100]}{'...' if len(user_text) > 100 else ''}")
            
            # Prepare prompt variables
            prompt_variables = {
                "customerMessage": user_text
            }
            
            # Add customer name if available
            if customer_name:
                prompt_variables["customerFirstName"] = customer_name
                logger.info(f"   Added customer name variable: {customer_name}")
            
            logger.info(f"   Prompt variables: {list(prompt_variables.keys())}")
            
            # Call OpenAI Prompts API
            logger.info("   Calling OpenAI Prompts API...")
            response = await self.client.responses.create(
                prompt={
                    "id": self.prompt_id,
                    "version": "2",
                    "variables": prompt_variables
                }
            )
            
            logger.info("   ✅ OpenAI Prompts response received")
            
            # Extract response content
            if response and hasattr(response, 'content'):
                ai_response = response.content
                logger.info(f"   Response length: {len(ai_response)} chars")
                logger.info(f"   Response preview: {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}")
                return ai_response
            else:
                logger.error("   ❌ No content in OpenAI response")
                return "Error: No response content received from OpenAI"
            
        except Exception as e:
            logger.error(f"   ❌ OpenAI Prompts API error: {type(e).__name__}: {str(e)}")
            return f"Error: {str(e)}"