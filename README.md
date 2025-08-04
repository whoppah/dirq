# Dixa Workflow API

FastAPI backend that exactly replicates the n8n Dixa automation workflow for processing conversation messages and generating AI responses with human oversight.

## Features

This application implements the complete n8n workflow with the following functionality:

✅ **Webhook Integration** - Receives Dixa conversation messages  
✅ **Initial Message Detection** - 5-second threshold logic for conversation starts  
✅ **OpenAI Assistant** - Processes messages using assistant `asst_ddwAna95PNJj3m0ZDmnVB7yf`  
✅ **Response Formatting** - Adds HTML confirmation buttons to AI responses  
✅ **Dixa API Integration** - Sends formatted responses back to conversations  
✅ **MongoDB Logging** - Persists conversation data and AI responses  
✅ **Human Oversight** - Yes/No confirmation buttons for response approval  
✅ **Queue Transfer** - Automatically transfers to human agents on rejection  

## Workflow Logic

```
Dixa Webhook → Message Detection → [Initial Message?] 
    ↓ Yes                              ↓ No
OpenAI Processing → Response Format → Skip (No-Op)
    ↓
Send to Dixa → Log to MongoDB → Await Confirmation
    ↓ No Response Rejected
Queue Transfer
```

## Setup

### Prerequisites
- Python 3.8+
- MongoDB instance
- OpenAI API key
- Dixa API access

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
```

3. **Update `.env` with your credentials:**
```env
DIXA_API_KEY=your_dixa_api_key
OPENAI_API_KEY=your_openai_api_key
MONGODB_URL=mongodb://localhost:27017/dirq
OPENAI_ASSISTANT_ID=asst_ddwAna95PNJj3m0ZDmnVB7yf
# ... other variables
```

4. **Run the application:**
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Main Endpoints
- `POST /dixa_conversation_started` - Main webhook for Dixa messages
- `GET /responded_false` - Handles "No" response confirmations
- `GET /health` - Health check endpoint
- `GET /` - Root endpoint with status

### API Documentation
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## Project Structure

```
├── main.py              # FastAPI application entry point
├── routes.py            # API route handlers
├── services.py          # Business logic services
├── models.py            # Pydantic models for validation
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore rules
└── project-steps.md    # Implementation roadmap
```

## Services

### OpenAIService
- Processes user messages using OpenAI Assistant API
- Manages conversation threads and message history
- Returns formatted AI responses

### MessageFormatter  
- Cleans text for JSON compatibility
- Adds HTML confirmation buttons to responses
- Formats payloads for Dixa API

### DixaAPIService
- Sends messages to Dixa conversations
- Transfers conversations to queues
- Handles Dixa API authentication

### MongoDBService
- Logs conversation data and AI responses
- Provides audit trail for all interactions
- Stores processing metadata

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DIXA_API_KEY` | Dixa API authentication key | Required |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_ASSISTANT_ID` | Specific assistant ID | `asst_ddwAna95PNJj3m0ZDmnVB7yf` |
| `DIXA_BASE_URL` | Dixa API base URL | `https://dev.dixa.io/v1` |
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017/dirq` |
| `AGENT_ID` | Dixa agent identifier | `65355895-3def-4735-aed4-82ef1f2b7000` |
| `QUEUE_ID` | Target queue for transfers | `d768da52-2eb2-4841-a5e8-ce2d7eed3f3f` |

## Deployment

The application is containerizable and can be deployed to any cloud platform:

```bash
# Production run
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Development

### Running Tests
```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when implemented)
pytest
```

### Contributing
1. Follow the existing code style and structure
2. Update tests for any new functionality  
3. Ensure all environment variables are documented
4. Update this README for significant changes

## Original n8n Workflow

This FastAPI application is a direct conversion from an n8n automation workflow, maintaining:
- Exact same processing logic
- Identical API integrations  
- Same hardcoded values and configurations
- Matching error handling patterns

## License

[Add your license information here]