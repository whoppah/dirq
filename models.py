from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

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
    tags: List[str] = []
    created_at: str

class MessageContent(BaseModel):
    text: str
    content_type: Optional[str] = None
    original_content_url: Optional[str] = None
    processed_content_url: Optional[str] = None

class Organization(BaseModel):
    id: str
    name: str

class MessageData(BaseModel):
    conversation: Conversation
    author: ContactPoint
    created_at: str
    message_id: str
    text: str
    direction: str
    channel: str
    content: MessageContent
    attachments: List[Any] = []
    external_id: Optional[str] = None

class WebhookPayload(BaseModel):
    event_id: str
    event_fqn: str
    event_version: str
    event_timestamp: str
    organization: Organization
    data: MessageData