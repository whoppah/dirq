from pydantic import BaseModel
from typing import Optional, List, Any
from .conversation import Conversation, ContactPoint, MessageContent

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