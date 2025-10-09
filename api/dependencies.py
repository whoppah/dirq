from functools import lru_cache
from core.services.openai_service import OpenAIService
from core.services.formatter_service import MessageFormatter
from core.services.dixa_service import DixaAPIService
from core.services.database_service import MongoDBService
from core.services.validation_service import ValidationService
from core.services.dashboard_service import DashboardAPIService

# Service factory functions with caching for singleton behavior
@lru_cache()
def get_openai_service() -> OpenAIService:
    return OpenAIService()

@lru_cache()
def get_message_formatter() -> MessageFormatter:
    return MessageFormatter()

@lru_cache()
def get_dixa_service() -> DixaAPIService:
    return DixaAPIService()

@lru_cache()
def get_mongodb_service() -> MongoDBService:
    return MongoDBService()

@lru_cache()
def get_validation_service() -> ValidationService:
    return ValidationService()

@lru_cache()
def get_dashboard_service() -> DashboardAPIService:
    return DashboardAPIService()

# Service container for easy access
class ServiceContainer:
    def __init__(self):
        self._openai_service = None
        self._message_formatter = None
        self._dixa_service = None
        self._mongodb_service = None
        self._validation_service = None
        self._dashboard_service = None
    
    @property
    def openai_service(self) -> OpenAIService:
        if self._openai_service is None:
            self._openai_service = get_openai_service()
        return self._openai_service
    
    @property
    def message_formatter(self) -> MessageFormatter:
        if self._message_formatter is None:
            self._message_formatter = get_message_formatter()
        return self._message_formatter
    
    @property
    def dixa_service(self) -> DixaAPIService:
        if self._dixa_service is None:
            self._dixa_service = get_dixa_service()
        return self._dixa_service
    
    @property
    def mongodb_service(self) -> MongoDBService:
        if self._mongodb_service is None:
            self._mongodb_service = get_mongodb_service()
        return self._mongodb_service
    
    @property
    def validation_service(self) -> ValidationService:
        if self._validation_service is None:
            self._validation_service = get_validation_service()
        return self._validation_service

    @property
    def dashboard_service(self) -> DashboardAPIService:
        if self._dashboard_service is None:
            self._dashboard_service = get_dashboard_service()
        return self._dashboard_service

# Global service container instance
services = ServiceContainer()