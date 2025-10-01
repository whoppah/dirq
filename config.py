import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DIXA_API_KEY = os.getenv("DIXA_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DIXA_BASE_URL = os.getenv("DIXA_BASE_URL", "https://dev.dixa.io/v1")
    AGENT_ID = os.getenv("AGENT_ID", "65355895-3def-4735-aed4-82ef1f2b7000")
    QUEUE_ID = os.getenv("QUEUE_ID", "d768da52-2eb2-4841-a5e8-ce2d7eed3f3f")
    OPENAI_PROMPT_ID = os.getenv("OPENAI_PROMPT_ID", "pmpt_68bcc4524178819485c37da997deecab093b3fe5540d118b")
    # Railway uses MONGO_URL, fallback to MONGODB_URL for local dev
    MONGODB_URL = os.getenv("MONGO_URL") or os.getenv("MONGODB_URL", "mongodb://localhost:27017/dirq")
    WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://your-webhook-url.com")

settings = Settings()