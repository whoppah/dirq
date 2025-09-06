#!/usr/bin/env python3
"""
Test script to validate the webhook payload against our Pydantic models
"""
import json
from models.webhook import WebhookPayload

# Your actual webhook payload with queue object
test_payload = {
  "event_id": "97183a78-1633-486e-93bc-776ce879c05f",
  "event_fqn": "CONVERSATION_MESSAGE_ADDED",
  "event_version": "1",
  "event_timestamp": "2025-09-04T16:11:44.847Z",
  "organization": {
    "id": "7c0308f4-8217-41e5-8dbe-725525c47ee3",
    "name": "Whoppah"
  },
  "data": {
    "conversation": {
      "csid": 46367,
      "channel": "EMAIL",
      "status": "OPEN",
      "direction": "INBOUND",
      "queue": {
        "id": "d0663131-8e7e-43a0-b5b4-629e4d6972dc",
        "name": "Whoppah high prio mail 🔥✉️"
      },
      "contact_point": "whoppah-support@email.dixa.io",
      "requester": {
        "id": "1c1ccdca-1777-4f28-a410-122437894006",
        "name": "modernariato design",
        "email": "modernariato.design@gmail.com",
        "phone": None,
        "roles": [],
        "user_type": "Contact"
      },
      "assignee": None,
      "subject": "https://www.poste.it/cerca/#/risultati-spedizioni/Ce010473861it",
      "tags": [
        {
          "id": "aaa7dafe-de97-3f29-aa38-9dee815af9e8",
          "name": "mim_notsucceeded",
          "is_deactivated": False
        },
        {
          "id": "d6cba639-aab0-38da-90b2-268e2e383037",
          "name": "shipping-delivery_confirmation",
          "is_deactivated": False
        },
        {
          "id": "e7e23eb9-4c99-3a26-8e0c-90fe28060bd4",
          "name": "mim_activated",
          "is_deactivated": False
        }
      ],
      "created_at": "2025-09-04T15:13:44.385Z"
    },
    "author": {
      "id": "1c1ccdca-1777-4f28-a410-122437894006",
      "name": "modernariato design",
      "email": "modernariato.design@gmail.com",
      "phone": None,
      "roles": [],
      "user_type": "Contact"
    },
    "created_at": "2025-09-04T16:11:44.847Z",
    "message_id": "2b102824-05a2-4175-8d25-b69e5ef1e919",
    "text": "Grazie. Ma Marcus Vohmann non risponde alla chat. Potete intervenire voi?\nGrazie.\nGiusy.\n\nIl gio 4 set 2025, 17:27 Sarie ha scritto:",
    "direction": "inbound",
    "channel": "EMAIL",
    "content": {
      "text": "Grazie. Ma Marcus Vohmann non risponde alla chat. Potete intervenire voi?\nGrazie.\nGiusy.\n\nIl gio 4 set 2025, 17:27 Sarie ha scritto:",
      "content_type": None,
      "original_content_url": "/private/7c0308f4-8217-41e5-8dbe-725525c47ee3/email_original_data/496225aeaebe0503249223268c85fa49_200ce360-d826-49e3-8799-f6c073d80f8f",
      "processed_content_url": None
    },
    "attachments": [],
    "external_id": None
  }
}

def test_webhook_validation():
    try:
        # Try to parse the payload with our Pydantic models
        webhook_payload = WebhookPayload(**test_payload)
        print("✅ Webhook payload validation successful!")
        print(f"Event: {webhook_payload.event_fqn}")
        print(f"Conversation ID: {webhook_payload.data.conversation.csid}")
        print(f"Author: {webhook_payload.data.author.email}")
        print(f"Tags: {[tag.name for tag in webhook_payload.data.conversation.tags]}")
        return True
    except Exception as e:
        print(f"❌ Webhook payload validation failed: {e}")
        return False

if __name__ == "__main__":
    test_webhook_validation()
