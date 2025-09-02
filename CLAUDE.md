# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run the application:**
```bash
python main.py
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Production deployment:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Railway deployment:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway link
railway up
```

**Development setup:**
```bash
cp .env.example .env
# Update .env with your credentials before running
```

## Architecture

This is a FastAPI application that replicates an n8n Dixa automation workflow. The architecture follows a service-oriented pattern:

**Core Services (services.py):**
- `OpenAIService` - Processes messages using OpenAI Assistant API with hardcoded assistant ID `asst_ddwAna95PNJj3m0ZDmnVB7yf`
- `MessageFormatter` - Cleans text and adds HTML confirmation buttons to AI responses  
- `DixaAPIService` - Handles Dixa API integration for sending messages and queue transfers
- `MongoDBService` - Logs all conversations and AI responses for audit trail
- `ValidationService` - Validates sender email domains (only whoppah.com allowed)

**Request Flow:**
1. Dixa webhook → `/dixa_conversation_started` endpoint (routes.py)
2. Domain validation checks if sender email is from whoppah.com
3. 5-second threshold check determines if message is conversation start
4. If domain valid AND initial message: OpenAI processing → response formatting → Dixa API → MongoDB logging
5. If validation fails: no-op (skip processing with reason)

**Key Configuration (config.py):**
- Uses environment variables with defaults for Dixa API, OpenAI, MongoDB connections
- Hardcoded agent/queue IDs match original n8n workflow exactly
- All configuration centralized in Settings class

**Critical Business Logic:**
- Message detection uses 5-second threshold between conversation creation and message timestamp
- AI responses include HTML confirmation buttons for human oversight
- "No" responses trigger automatic queue transfer to human agents
- All processing decisions and responses are logged to MongoDB

The codebase maintains exact compatibility with the original n8n workflow, including hardcoded values, API patterns, and processing logic.