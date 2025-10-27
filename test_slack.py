"""
Quick test script to verify Slack integration
"""
import asyncio
from core.services.slack_service import SlackService

async def test_slack():
    slack_service = SlackService()
    
    result = await slack_service.send_notification(
        user_email="test@example.com",
        user_message="This is a test message from the Dixa AI system",
        ai_response="This is a test AI response to verify the Slack integration is working correctly.",
        conversation_id="TEST-123",
        additional_context={
            "handoff_required": False,
            "is_initial_message": True,
            "test_mode": True
        }
    )
    
    if result["success"]:
        print("✅ Slack test message sent successfully!")
        print(f"Response: {result}")
    else:
        print("❌ Slack test failed!")
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_slack())
