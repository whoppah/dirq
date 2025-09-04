from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class Tag(BaseModel):
    id: str
    name: str
    is_deactivated: bool

class ContactPoint(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    roles: List[str] = []
    user_type: str

class Conversation(BaseModel):
    csid: int
    channel: str
    status: str
    direction: str
    queue: Optional[str] = None
    contact_point: str
    requester: ContactPoint
    assignee: Optional[ContactPoint] = None
    subject: str
    tags: List[Tag] = []
    created_at: str

class MessageContent(BaseModel):
    text: str
    content_type: Optional[str] = None
    original_content_url: Optional[str] = None
    processed_content_url: Optional[str] = None