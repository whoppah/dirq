"""
Simple synchronous test for Slack integration
"""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import settings

def test_slack_simple():
    print("Testing Slack integration...")
    print(f"Bot Token: {settings.SLACK_BOT_TOKEN[:20]}..." if settings.SLACK_BOT_TOKEN else "Bot Token: NOT SET")
    print(f"Channel: {settings.SLACK_CHANNEL_ID}")
    
    if not settings.SLACK_BOT_TOKEN:
        print("❌ SLACK_BOT_TOKEN not configured!")
        return
    
    try:
        client = WebClient(token=settings.SLACK_BOT_TOKEN)
        
        # Send a simple test message
        response = client.chat_postMessage(
            channel=settings.SLACK_CHANNEL_ID,
            text="🧪 Test message from Dixa AI - Slack integration is working!"
        )
        
        if response["ok"]:
            print("✅ Slack test message sent successfully!")
            print(f"Message timestamp: {response['ts']}")
            print(f"Channel: {response['channel']}")
        else:
            print("❌ Slack API returned not OK")
            print(f"Response: {response}")
            
    except SlackApiError as e:
        print(f"❌ Slack API Error: {e.response['error']}")
        print(f"Full error: {e}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    test_slack_simple()
