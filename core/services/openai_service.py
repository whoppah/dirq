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
            # Create a thread
            thread = await self.client.beta.threads.create()
            
            # Add the user message to the thread
            await self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Users email:\n {user_text}"  # Exact format from n8n
            )
            
            # Run the assistant
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Wait for completion
            while run.status in ["queued", "in_progress"]:
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                # Get the assistant's response
                messages = await self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                
                # Get the latest assistant message
                for message in messages.data:
                    if message.role == "assistant":
                        return message.content[0].text.value
                        
            logger.error(f"OpenAI run failed with status: {run.status}")
            return "Error: Could not generate response"
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return f"Error: {str(e)}"