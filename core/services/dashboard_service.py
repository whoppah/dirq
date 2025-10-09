import logging
import httpx
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)

class DashboardAPIService:
    """
    Service for fetching user context data from Whoppah Dashboard API
    Provides real-time user data (orders, threads, stats) for OpenAI processing
    """

    def __init__(self):
        self.api_url = settings.DASHBOARD_API_URL
        self.api_token = settings.DASHBOARD_API_TOKEN
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }

    async def get_user_context(self, email: str, orders_limit: int = 10, threads_limit: int = 10) -> Optional[Dict[str, Any]]:
        """
        Fetch user context data from Dashboard API

        Args:
            email: User's email address
            orders_limit: Maximum number of orders to return (default: 10)
            threads_limit: Maximum number of message threads to return (default: 10)

        Returns:
            Dictionary containing user profile, orders, threads, and stats, or None if error
        """
        try:
            logger.info(f"📊 DASHBOARD API - Fetching user context for {email}")

            params = {
                "email": email,
                "orders_limit": orders_limit,
                "threads_limit": threads_limit
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.api_url,
                    headers=self.headers,
                    params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"   ✅ Successfully fetched user context")
                    logger.info(f"   Orders: {data.get('stats', {}).get('total_orders', 0)}, Threads: {data.get('stats', {}).get('total_threads', 0)}")
                    return data
                elif response.status_code == 404:
                    logger.warning(f"   ⚠️  User not found in Dashboard API: {email}")
                    return None
                else:
                    logger.error(f"   ❌ Dashboard API error: {response.status_code} - {response.text}")
                    return None

        except httpx.TimeoutException:
            logger.error(f"   ❌ Dashboard API timeout for email: {email}")
            return None
        except Exception as e:
            logger.error(f"   ❌ Error fetching user context from Dashboard API: {str(e)}")
            return None

    def format_user_context(self, context: Dict[str, Any]) -> str:
        """
        Format user context data into a readable string for OpenAI

        Args:
            context: User context data from Dashboard API

        Returns:
            Formatted string with user context information
        """
        parts = ["=== USER CONTEXT DATA ===\n"]

        # User profile information
        if "user" in context:
            user = context["user"]
            parts.append("User Profile:")
            parts.append(f"  Name: {user.get('name', 'N/A')}")
            parts.append(f"  Email: {user.get('email', 'N/A')}")
            parts.append(f"  User ID: {user.get('id', 'N/A')}")
            parts.append(f"  Account Created: {user.get('created_at', 'N/A')}")
            parts.append("")

        # Statistics
        if "stats" in context:
            stats = context["stats"]
            parts.append("User Statistics:")
            parts.append(f"  Total Orders: {stats.get('total_orders', 0)}")
            parts.append(f"  Total Threads: {stats.get('total_threads', 0)}")
            parts.append("")

        # Recent orders
        if "orders" in context and context["orders"]:
            parts.append(f"Recent Orders ({len(context['orders'])} total):")
            for order in context["orders"][:5]:  # Show first 5
                parts.append(f"  - Order #{order.get('id', 'N/A')}")
                parts.append(f"    Status: {order.get('status', 'N/A')}")
                parts.append(f"    Total: €{order.get('total_price', 0)}")
                parts.append(f"    Created: {order.get('created_at', 'N/A')}")
                if order.get('items'):
                    parts.append(f"    Items: {len(order['items'])}")
            parts.append("")

        # Recent message threads
        if "threads" in context and context["threads"]:
            parts.append(f"Recent Message Threads ({len(context['threads'])} total):")
            for thread in context["threads"][:3]:  # Show first 3
                parts.append(f"  - Thread #{thread.get('id', 'N/A')}")
                parts.append(f"    Subject: {thread.get('subject', 'N/A')}")
                parts.append(f"    Status: {thread.get('status', 'N/A')}")
                parts.append(f"    Messages: {thread.get('message_count', 0)}")
                parts.append(f"    Last Updated: {thread.get('updated_at', 'N/A')}")
            parts.append("")

        parts.append("=== END USER CONTEXT ===")

        return "\n".join(parts)
