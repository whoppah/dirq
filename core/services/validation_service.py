import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

class ValidationService:
    """
    Service for validating webhook requests and email domains
    """
    
    def __init__(self):
        self.allowed_domains = ["whoppah.com"]
    
    def is_email_from_allowed_domain(self, email: str) -> Tuple[bool, str]:
        """
        Check if email is from an allowed domain (whoppah.com)
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            if not email or not isinstance(email, str):
                return False, "Invalid email format"
            
            # Extract domain from email
            email_pattern = r'^[^@]+@([^@]+)$'
            match = re.match(email_pattern, email.lower().strip())
            
            if not match:
                return False, "Invalid email format"
            
            domain = match.group(1)
            
            # Check if domain is in allowed list
            if domain in self.allowed_domains:
                logger.info(f"Email domain validated: {domain}")
                return True, f"Allowed domain: {domain}"
            else:
                logger.info(f"Email domain rejected: {domain} (not in allowed domains: {self.allowed_domains})")
                return False, f"Domain not allowed: {domain}"
                
        except Exception as e:
            logger.error(f"Error validating email domain: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def should_process_message(self, author_email: str, is_initial_message: bool) -> Tuple[bool, str]:
        """
        Determine if message should be processed based on domain and initial message check
        
        Args:
            author_email: Email of the message author
            is_initial_message: Whether this is an initial message (5-second threshold)
            
        Returns:
            Tuple of (should_process, reason)
        """
        # First check if it's an initial message
        if not is_initial_message:
            return False, "Not an initial message (5-second threshold not met)"
        
        # Then check domain validation
        domain_valid, domain_reason = self.is_email_from_allowed_domain(author_email)
        if not domain_valid:
            return False, f"Domain validation failed: {domain_reason}"
        
        return True, f"Processing allowed: Initial message from {domain_reason}"