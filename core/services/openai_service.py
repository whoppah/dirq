import logging
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.assistant_id = settings.OPENAI_ASSISTANT_ID
    
    async def process_message(self, user_text: str) -> str:
        """
        Process user message using OpenAI Assistant API
        Matches the exact OpenAI node configuration from n8n
        """
        try:
            logger.info("🤖 OPENAI SERVICE - Starting message processing")
            logger.info(f"   Assistant ID: {self.assistant_id}")
            logger.info(f"   Input text length: {len(user_text)} chars")
            logger.info(f"   Input preview: {user_text[:100]}{'...' if len(user_text) > 100 else ''}")
            
            # Create a thread
            logger.info("   Creating OpenAI thread...")
            thread = await self.client.beta.threads.create()
            logger.info(f"   ✅ Thread created: {thread.id}")
            
            # Add the user message to the thread
            formatted_content = f"Users email:\n {user_text}"  # Exact format from n8n
            logger.info("   Adding message to thread...")
            logger.info(f"   Formatted content: {formatted_content[:150]}{'...' if len(formatted_content) > 150 else ''}")
            
            await self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=formatted_content
            )
            logger.info("   ✅ Message added to thread")
            
            # Run the assistant
            logger.info("   Starting assistant run...")
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            logger.info(f"   ✅ Run created: {run.id}")
            logger.info(f"   Initial status: {run.status}")
            
            # Wait for completion
            poll_count = 0
            while run.status in ["queued", "in_progress"]:
                poll_count += 1
                logger.info(f"   Polling run status... (attempt {poll_count}) - Status: {run.status}")
                
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                
                # Add a small delay to avoid excessive polling
                if run.status in ["queued", "in_progress"]:
                    import asyncio
                    await asyncio.sleep(1)
            
            logger.info(f"   Final run status: {run.status}")
            
            if run.status == "completed":
                logger.info("   ✅ Run completed successfully - Retrieving messages...")
                
                # Get the assistant's response
                messages = await self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                
                logger.info(f"   Retrieved {len(messages.data)} messages from thread")
                
                # Get the latest assistant message
                for i, message in enumerate(messages.data):
                    logger.info(f"   Message {i}: Role={message.role}, Content length={len(message.content[0].text.value) if message.content else 0}")
                    if message.role == "assistant":
                        response_text = message.content[0].text.value
                        logger.info(f"   ✅ Assistant response found: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
                        logger.info(f"   Response length: {len(response_text)} chars")
                        return response_text
                
                logger.error("   ❌ No assistant message found in thread")
                return "Error: No assistant response found"
            else:
                logger.error(f"   ❌ OpenAI run failed with status: {run.status}")
                if hasattr(run, 'last_error') and run.last_error:
                    logger.error(f"   Error details: {run.last_error}")
                return "Error: Could not generate response"
            
        except Exception as e:
            logger.error(f"   ❌ OpenAI API error: {type(e).__name__}: {str(e)}")
            return f"Error: {str(e)}"