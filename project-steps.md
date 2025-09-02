# Dixa Workflow Conversion Project Steps

## Overview
Converting an n8n automation workflow to a Node.js application that exactly replicates the existing workflow functionality.

## Workflow Analysis (From JSON)
The n8n workflow consists of these exact nodes:
1. **Webhook** - POST `/dixa_conversation_started` - Receives Dixa conversation messages
2. **Code** - Python script for initial message detection (5-second threshold)
3. **If** - Conditional check for `isInitialMessage === true`
4. **OpenAI** - Assistant API call with assistant `asst_ddwAna95PNJj3m0ZDmnVB7yf`
5. **Json converter + webhook** - Python script that formats response and adds webhook buttons
6. **Send Email with webhook included** - HTTP POST to Dixa API to send message
7. **Postgres** - Database operation (schema/table not specified in JSON)
8. **Webhook for Response No** - GET `/responded_false` endpoint
9. **Transfer Queue** - HTTP PUT to transfer conversation to queue on "No" response
10. **No Operation, do nothing** - For non-initial messages

## Implementation Steps

### Step 1: Project Setup
- [x] Initialize Python FastAPI project
- [x] Install dependencies: fastapi, uvicorn, openai, httpx, pymongo, python-dotenv
- [x] Create basic project structure

### Step 2: Main Webhook Endpoint
- [x] Create POST `/dixa_conversation_started` FastAPI endpoint
- [x] Parse incoming Dixa webhook payload structure using Pydantic models

### Step 3: Initial Message Detection
- [x] Implement exact Python logic from n8n:
  - Extract `conversation.created_at` and `data.created_at`
  - Convert to datetime objects
  - Calculate time difference in milliseconds
  - Set `isInitialMessage = time_diff <= 5000`

### Step 4: Conditional Processing
- [x] Add if condition to only process when `isInitialMessage === true`
- [x] Skip processing for non-initial messages (no-op)

### Step 5: OpenAI Assistant Integration
- [x] Set up OpenAI client
- [x] Use exact assistant ID: `asst_ddwAna95PNJj3m0ZDmnVB7yf`
- [x] Send user email text: `{{ $json.body.data.text }}`

### Step 6: Response Formatting
- [x] Implement exact Python logic from "Json converter + webhook" node:
  - Clean text for JSON using regex patterns
  - Add hardcoded webhook buttons HTML
  - Use exact Dixa API payload structure

### Step 7: Send Message to Dixa
- [x] HTTP POST to `https://dev.dixa.io/v1/conversations/{conversationId}/messages` using httpx
- [x] Use exact headers and payload structure from JSON
- [x] Handle conversation ID dynamically (currently hardcoded as 33332)

### Step 8: Database Integration
- [x] Add MongoDB connection using pymongo
- [x] Create collection for conversation logging (minimal implementation)

### Step 9: Response Webhook
- [x] Create GET `/responded_false` FastAPI endpoint
- [x] No processing logic specified in JSON

### Step 10: Queue Transfer
- [x] HTTP PUT to `https://dev.dixa.io/v1/conversations/33332/transfer/queue` using httpx
- [x] Use exact payload: `{"queueId": "d768da52-2eb2-4841-a5e8-ce2d7eed3f3f", "userId": user_id}`

## Technical Details (Exact from JSON)

### Hardcoded Values (as in JSON):
- **Dixa API Key**: `eyJhbGciOiJIUzI1NiJ9...` (move to env)
- **Agent ID**: `65355895-3def-4735-aed4-82ef1f2b7000` 
- **Queue ID**: `d768da52-2eb2-4841-a5e8-ce2d7eed3f3f`
- **OpenAI Assistant**: `asst_ddwAna95PNJj3m0ZDmnVB7yf`
- **Conversation ID**: 33332 (hardcoded, needs to be dynamic)
- **Dixa Base URL**: `https://dev.dixa.io/v1`

### Exact Webhook HTML (from JSON):
```html
<p>Please confirm your response:</p>

<a href="https://your-webhook-url.com/respond?answer=yes"
   style="display: inline-block; padding: 10px 20px; margin-right: 10px; background-color: #28a745; color: white; text-decoration: none; border-radius: 4px;">
   Yes
</a>

<a href="https://your-webhook-url.com/responded_false"
   style="display: inline-block; padding: 10px 20px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 4px;">
   No
</a>
```

### API Endpoints (Exact from JSON):
- `POST /dixa_conversation_started` - Main webhook
- `GET /responded_false` - Response webhook

## Notes from JSON Analysis
- Conversation ID is hardcoded as 33332 in HTTP requests
- Agent ID varies between nodes (inconsistent in original)
- PostgreSQL node has no specific operation defined
- "Transfer Queue" only triggers on "No" response
- Webhook buttons have placeholder URLs that need to be updated