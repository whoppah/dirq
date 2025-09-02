from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "dixa-webhook"}

@router.get("/")
async def root():
    return {"message": "Dixa Workflow API is running"}