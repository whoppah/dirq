import logging
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from config import settings
import threading

logger = logging.getLogger(__name__)

class MongoDBService:
    """
    Service for MongoDB operations
    Minimal implementation for conversation logging as per n8n Postgres node
    Uses thread-safe singleton pattern to ensure only one connection is established
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    logger.info("Creating new MongoDBService singleton instance")
                    cls._instance = super(MongoDBService, cls).__new__(cls)
                    cls._instance._init_connection()
        return cls._instance

    def _init_connection(self):
        """Initialize MongoDB connection - called only once"""
        try:
            logger.info(f"🔌 Initializing MongoDB connection: {settings.MONGODB_URL[:50]}...")
            self.client = MongoClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Test the connection
            self.client.admin.command('ping')

            # Extract database name from URL or use default
            if settings.MONGODB_URL and '/' in settings.MONGODB_URL:
                db_name = settings.MONGODB_URL.split('/')[-1].split('?')[0]
                if db_name and db_name != '':
                    self.db = self.client[db_name]
                else:
                    self.db = self.client['dirq']
            else:
                self.db = self.client['dirq']

            self.conversations_collection = self.db.conversations
            self.idempotency_collection = self.db.idempotency

            # Create TTL index on idempotency collection
            try:
                self.idempotency_collection.create_index(
                    "reserved_at",
                    expireAfterSeconds=90
                )
                logger.info("✅ TTL index created on idempotency collection (90 sec expiry)")
            except Exception as idx_err:
                logger.warning(f"⚠️  TTL index creation warning: {idx_err}")

            logger.info(f"✅ MongoDB connected successfully to database: {self.db.name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None
    
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

    async def try_reserve_message(self, event_id: str) -> bool:
        """
        Attempt to reserve processing for a given event_id. Returns True if
        reservation acquired, False if already reserved elsewhere.
        CRITICAL: If MongoDB is unavailable, we BLOCK (return False) to prevent duplicates.
        """
        try:
            if not self.client:
                logger.error("MongoDB not connected - blocking webhook to prevent duplicate sends")
                return False
            # Use _id for uniqueness so we don't rely on create_index permissions
            self.idempotency_collection.insert_one({
                "_id": event_id,
                "event_id": event_id,
                "reserved_at": datetime.utcnow()
            })
            logger.info(f"✅ Reservation acquired for event {event_id}")
            return True
        except DuplicateKeyError:
            # Already reserved by another concurrent process
            logger.warning(f"⚠️ Duplicate detected: Event {event_id} already reserved")
            return False
        except Exception as e:
            logger.error(f"❌ Error reserving event idempotency token: {str(e)}")
            # Fail-closed to prevent duplicate sends when DB has issues
            return False

    async def release_reservation(self, event_id: str) -> None:
        """
        Release a previously acquired reservation. Safe to call even if no token
        exists or DB is unavailable.
        """
        try:
            if not self.client:
                return
            self.idempotency_collection.delete_one({"_id": event_id})
        except Exception as e:
            logger.warning(f"Error releasing idempotency reservation: {str(e)}")

    async def has_event_been_processed(self, event_id: str) -> bool:
        """
        Check if an event_id has already been processed (logged to conversations).
        Returns True if the event exists in conversations collection, regardless of
        whether a message was sent (includes both processed and skipped events).
        """
        try:
            if not self.client:
                return False
            doc = self.conversations_collection.find_one({
                "event_id": event_id
            })
            return doc is not None
        except Exception as e:
            logger.error(f"Error checking if event was already processed: {str(e)}")
            return False