from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from utils.logging import setup_logging, get_logger
from api.routes import webhook, health

load_dotenv()

# Configure logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Dixa Workflow API",
    description="FastAPI backend that replicates n8n Dixa automation workflow",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(webhook.router, tags=["webhook"])
app.include_router(health.router, tags=["health"])

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)