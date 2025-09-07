import logging
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from config import settings

logger = logging.getLogger(__name__)

class MongoDBService:
    """
    Service for MongoDB operations
    Minimal implementation for conversation logging as per n8n Postgres node
    """
    
    def __init__(self):
        try:
            self.client = MongoClient(settings.MONGODB_URL)
            self.db = self.client.get_default_database()
            self.conversations_collection = self.db.conversations
            # Collection for idempotency tokens
            self.idempotency_collection = self.db.idempotency
            try:
                # Ensure a unique index on message_id for idempotency reservations
                self.idempotency_collection.create_index("message_id", unique=True)
            except Exception as idx_err:
                logger.warning(f"Idempotency index creation warning: {idx_err}")
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
    
    async def log_conversation(self, conversation_data: dict) -> dict:
        """
        Log conversation data to MongoDB
        Minimal implementation matching n8n Postgres node functionality
        """
        try:
            if not self.client:
                return {"success": False, "error": "MongoDB not connected"}
            
            # Add timestamp
            conversation_data["logged_at"] = datetime.utcnow()
            
            # Insert the document
            result = self.conversations_collection.insert_one(conversation_data)
            
            logger.info(f"Logged conversation {conversation_data.get('conversation_id')} to MongoDB")
            return {
                "success": True,
                "inserted_id": str(result.inserted_id)
            }
            
        except Exception as e:
            logger.error(f"Error logging to MongoDB: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def has_message_been_sent(self, message_id: str) -> bool:
        """
        Check if a message with the given message_id has already resulted
        in a sent Dixa message (idempotency guard).
        We rely on the existing 'conversations' collection where we store
        documents that include `message_id` and `dixa_message_sent: True`.
        """
        try:
            if not self.client:
                return False
            doc = self.conversations_collection.find_one({
                "message_id": message_id,
                "dixa_message_sent": True
            })
            return doc is not None
        except Exception as e:
            logger.error(f"Error checking if message was already sent: {str(e)}")
            return False

    async def try_reserve_message(self, message_id: str) -> bool:
        """
        Attempt to reserve processing for a given message_id. Returns True if
        reservation acquired, False if already reserved elsewhere.
        If MongoDB is unavailable, allow processing to proceed (return True).
        """
        try:
            if not self.client:
                return True
            # Use _id for uniqueness so we don't rely on create_index permissions
            self.idempotency_collection.insert_one({
                "_id": message_id,
                "message_id": message_id,
                "reserved_at": datetime.utcnow()
            })
            return True
        except DuplicateKeyError:
            # Already reserved by another concurrent process
            return False
        except Exception as e:
            logger.error(f"Error reserving message idempotency token: {str(e)}")
            # Fail-open to avoid blocking the flow completely
            return True

    async def release_reservation(self, message_id: str) -> None:
        """
        Release a previously acquired reservation. Safe to call even if no token
        exists or DB is unavailable.
        """
        try:
            if not self.client:
                return
            self.idempotency_collection.delete_one({"_id": message_id})
        except Exception as e:
            logger.warning(f"Error releasing idempotency reservation: {str(e)}")

    async def has_event_been_processed(self, event_id: str) -> bool:
        """
        Check if an event_id has already been processed (message sent and logged).
        """
        try:
            if not self.client:
                return False
            doc = self.conversations_collection.find_one({
                "event_id": event_id,
                "dixa_message_sent": True
            })
            return doc is not None
        except Exception as e:
            logger.error(f"Error checking if event was already processed: {str(e)}")
            return False