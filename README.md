# Dirq - Whoppah AI Customer Support Agent

**Dirq** (Dixa + AI Request Queue) is an intelligent customer support automation system for Whoppah marketplace. It receives customer emails via Dixa webhooks, processes them with AI using OpenAI's Prompts API, and sends contextual, helpful responses back to customers—all while maintaining human oversight and seamless handoff capabilities.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [AI Prompt System](#ai-prompt-system)
- [Idempotency & Duplicate Handling](#idempotency--duplicate-handling)
- [Deployment](#deployment)
- [MCP Integration (Planned)](#mcp-integration-planned)
- [Development](#development)
- [Monitoring & Debugging](#monitoring--debugging)

---

## Overview

Dirq automates Whoppah's customer support by:

1. **Receiving** customer messages from Dixa (customer service platform)
2. **Processing** messages with OpenAI to generate intelligent, context-aware responses
3. **Searching** Whoppah's FAQ database for accurate information
4. **Sending** formatted responses back to customers via Dixa
5. **Handing off** to human agents when needed (complex cases, explicit requests, etc.)
6. **Logging** all interactions to MongoDB for audit trail and analytics

### Problem It Solves

- **Reduces response time**: Instant AI-generated responses for common inquiries
- **Scales support**: Handles unlimited concurrent customer conversations
- **Maintains quality**: Follows strict guidelines, uses only verified FAQ information
- **Smart escalation**: Automatically hands off complex cases to humans
- **Consistent experience**: Same high-quality responses regardless of time/volume

---

## Key Features

### ✅ **Intelligent Webhook Processing**
- Receives Dixa conversation webhooks via POST endpoint
- Validates message authenticity and processes only initial messages (5-second threshold)
- Domain filtering with whitelist/blacklist support (whoppah.com, whoppah.nl, specific emails)

### ✅ **AI-Powered Response Generation**
- Uses OpenAI Prompts API with custom Whoppah Support prompt
- Searches FAQ database for accurate information
- Supports multiple languages (NL, EN, DE, FR, IT)
- Detects customer role (buyer vs seller) for contextual responses
- Formats responses with bold text, proper structure, and FAQ links

### ✅ **Smart Handoff System**
- 9 mandatory handoff scenarios (cancellations, refunds, shipping label issues, etc.)
- Automatic handoff after 2 customer interactions
- Clean, professional handoff messages
- No false promises or information after handoff

### ✅ **Robust Idempotency**
- Thread-safe MongoDB singleton pattern
- Duplicate webhook detection and prevention
- Event-based reservation system with TTL (5-minute auto-cleanup)
- Checks conversations collection first for fastest duplicate detection

### ✅ **Production-Ready Architecture**
- FastAPI with async/await for high performance
- Comprehensive error logging with stack traces
- MongoDB audit trail for all interactions
- Health check endpoint for monitoring
- Railway deployment ready

### ✅ **Human Oversight (Future)**
- Confirmation buttons in email responses
- "Did we resolve your problem?" Yes/No workflow
- Automatic queue transfer on negative responses

---

## Architecture

### High-Level Flow

```
┌─────────────┐
│ Customer    │ Sends email to whoppah-support@email.dixa.io
│ (Buyer/Seller)│
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Dixa Platform                                                │
│ - Receives email                                             │
│ - Creates conversation                                       │
│ - Sends webhook to Dirq                                      │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Dirq (This Application)                                      │
│                                                               │
│  Step 1: Idempotency Check                                   │
│  ├─ Check if event already processed (MongoDB)               │
│  └─ Acquire reservation (prevent concurrent processing)      │
│                                                               │
│  Step 2: Validation                                          │
│  ├─ Is initial message? (5-second threshold)                 │
│  └─ Is from allowed domain? (whoppah.com, whitelist)         │
│                                                               │
│  Step 3: AI Processing (if validation passes)                │
│  ├─ Detect language (NL, EN, DE, FR, IT)                     │
│  ├─ Detect role (buyer vs seller)                            │
│  ├─ Detect intent (refund, payout, shipping, etc.)           │
│  ├─ Check handoff scenarios (9 types)                        │
│  ├─ Search FAQ database                                      │
│  └─ Generate response via OpenAI Prompts API                 │
│                                                               │
│  Step 4: Response Formatting                                 │
│  ├─ Clean text for JSON compatibility                        │
│  ├─ Add bold formatting for key info                         │
│  └─ Add FAQ link (max 1)                                     │
│                                                               │
│  Step 5: Send to Dixa                                        │
│  └─ POST to Dixa conversations API                           │
│                                                               │
│  Step 6: Logging                                             │
│  └─ Store in MongoDB (conversations collection)              │
│                                                               │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│ Customer    │ Receives AI-generated response in Dixa
│             │
└─────────────┘
```

### Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **AI**: OpenAI Prompts API (GPT-4/5)
- **Database**: MongoDB (with TTL indexes for auto-cleanup)
- **Customer Platform**: Dixa API
- **Deployment**: Railway (with auto-deploy from GitHub)
- **Logging**: Python logging with structured output

---

## How It Works

### 1. Webhook Reception

When a customer emails Whoppah Support, Dixa creates a conversation and sends a webhook to Dirq:

```json
{
  "event_id": "unique-event-id",
  "event_fqn": "CONVERSATION_MESSAGE_ADDED",
  "data": {
    "conversation": {
      "csid": 12345,
      "created_at": "2025-10-06T10:00:00.000Z"
    },
    "author": {
      "name": "Anna",
      "email": "anna@example.com"
    },
    "message_id": "msg-id",
    "text": "Customer's message here",
    "created_at": "2025-10-06T10:00:00.045Z"
  }
}
```

### 2. Idempotency & Duplicate Prevention

**Problem**: Dixa often sends the same webhook 2-3 times simultaneously.

**Solution**: Two-layer idempotency check:

1. **Check conversations collection** (MongoDB) - fastest path
   - If `event_id` exists → return "duplicate_ignored"

2. **Acquire reservation** (idempotency collection)
   - Try to insert `event_id` as `_id` (unique constraint)
   - If duplicate key error → another request is processing → return "duplicate_ignored"
   - If success → proceed with processing

3. **Log completion** to conversations collection
   - This ensures step 1 catches future duplicates immediately

4. **TTL cleanup** (5 minutes)
   - Stale reservations auto-expire
   - Prevents orphaned locks

### 3. Validation

Two checks determine if message should be processed:

**A. Initial Message Detection**
```python
time_diff = (message_created - conversation_created) in milliseconds
is_initial = time_diff <= 5000  # 5 second threshold
```

**B. Domain Validation**
```python
Whitelist: ["mrlkns@gmail.com", "sariewalburghschmidt@hotmail.com", ...]
Allowed domains: ["whoppah.com", "whoppah.nl"]
Blacklist: []
```

If **both pass** → proceed to AI processing
If **either fails** → log as skipped, return success

### 4. AI Processing

**Prompt Variables Sent:**
```python
{
  "customerFirstName": "Anna",  # Extracted from author.name
  "email": "Customer's message text"
}
```

**AI Response Received:**
```json
{
  "email": "Dear Anna,\n\nThank you for your question...\n\nBest regards,\nAnna"
}
```

The AI follows a comprehensive prompt that:
- Detects language and responds in same language
- Identifies buyer vs seller context
- Searches FAQ database for accurate info
- Follows strict formatting rules (bold text, max 150 words)
- Triggers handoff in 9 specific scenarios
- Never makes promises it can't keep

### 5. Handoff Scenarios

AI automatically hands off to human in these cases:

1. **Talk to Human** - Customer explicitly requests human agent
2. **Shipping Label Issues** - Can't generate shipping label
3. **Cancellation Request** - Customer wants to cancel order
4. **Refund Request** - Customer explicitly requests refund
5. **Contact Support Scenarios** - FAQ says "contact support"
6. **After 2 Interactions** - Customer replied twice (auto-handoff on 3rd response)
7. **Delivery Confirmation** - Customer confirms delivery
8. **Meeting/Appointment Requests** - Any scheduling requests (Brenger, calls, etc.)
9. **Other Escalations** - Phone calls, complex disputes, technical issues

**Handoff Response Format:**
```
Dear Anna,

Thank you for your email.

I'll connect you with a colleague who can help you better with this.

Best regards,
Anna
```

### 6. Response Formatting & Sending

**Formatter adds:**
- HTML confirmation buttons (for future human oversight)
- Proper text cleaning (JSON-safe)
- Dixa API payload structure

**Sent to Dixa:**
```json
{
  "agentId": "agent-uuid",
  "content": {
    "_type": "Text",
    "value": "Formatted HTML response",
    "contentType": "text/html"
  },
  "_type": "Outbound"
}
```

### 7. MongoDB Logging

Every processed message (success or skipped) is logged:

```json
{
  "_id": "ObjectId",
  "conversation_id": 12345,
  "message_id": "msg-id",
  "event_id": "unique-event-id",
  "user_id": "user-uuid",
  "ai_response": "Dear Anna...",
  "is_initial_message": true,
  "time_diff_ms": 45,
  "dixa_message_sent": true,
  "original_text": "Customer's message",
  "logged_at": "2025-10-06T10:00:05.000Z",
  "skipped_reason": null  // or reason if skipped
}
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- MongoDB 5.0+ (local or Railway)
- OpenAI API key with Prompts API access
- Dixa API key
- Railway CLI (for deployment)

### Local Development Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd dirq
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
```

5. **Update `.env` with your credentials:**
```env
# Dixa Configuration
DIXA_API_KEY=your_dixa_api_key_here
DIXA_BASE_URL=https://dev.dixa.io/v1
AGENT_ID=your-agent-uuid
QUEUE_ID=your-queue-uuid

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_PROMPT_ID=pmpt_68bcc4524178819485c37da997deecab093b3fe5540d118b

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017/dirq
# Or for Railway: mongodb://user:pass@host:port/dirq?authSource=admin

# Webhook Configuration (for button links)
WEBHOOK_BASE_URL=http://localhost:8000
```

6. **Run the application:**
```bash
python main.py
```

The API will be available at `http://localhost:8000`

**Test it:**
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

---

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DIXA_API_KEY` | Dixa API authentication key | ✅ Yes | - |
| `DIXA_BASE_URL` | Dixa API base URL | No | `https://dev.dixa.io/v1` |
| `AGENT_ID` | Dixa agent UUID for sending messages | ✅ Yes | - |
| `QUEUE_ID` | Dixa queue UUID for transfers | ✅ Yes | - |
| `OPENAI_API_KEY` | OpenAI API key | ✅ Yes | - |
| `OPENAI_PROMPT_ID` | OpenAI Prompt template ID | ✅ Yes | - |
| `OPENAI_MODEL` | OpenAI model to use | No | `gpt-5` |
| `MONGODB_URL` | MongoDB connection string | ✅ Yes | - |
| `WEBHOOK_BASE_URL` | Base URL for webhook callbacks | No | `https://your-app.railway.app` |

### MongoDB Setup

**Local MongoDB:**
```bash
# Start MongoDB
mongod --dbpath /path/to/data

# Connection string
MONGODB_URL=mongodb://localhost:27017/dirq
```

**Railway MongoDB:**
```bash
# Railway auto-generates this, but you need to add database name
MONGODB_URL=mongodb://user:pass@host:port/dirq?authSource=admin
```

**Collections Created:**
- `conversations` - All processed messages (with `event_id` index)
- `idempotency` - Event reservations (with TTL index, 5-min expiry)

---

## API Endpoints

### Main Endpoints

#### `POST /dixa_conversation_started`
Main webhook endpoint for Dixa conversation messages.

**Request Body:**
```json
{
  "event_id": "string",
  "event_fqn": "CONVERSATION_MESSAGE_ADDED",
  "data": {
    "conversation": { ... },
    "author": { ... },
    "message_id": "string",
    "text": "string",
    "created_at": "ISO 8601 timestamp"
  }
}
```

**Response (Success):**
```json
{
  "status": "processed_and_sent",
  "conversation_id": 12345,
  "message_id": "msg-id",
  "isInitialMessage": true,
  "ai_response": "Dear Anna...",
  "message_sent": true,
  "logged_to_db": true
}
```

**Response (Duplicate):**
```json
{
  "status": "duplicate_ignored",
  "conversation_id": 12345,
  "event_id": "event-id",
  "reason": "Event already processed (logged in database)"
}
```

**Response (Skipped):**
```json
{
  "status": "ignored",
  "conversation_id": 12345,
  "validation_reason": "Not an initial message",
  "reason": "Validation failed or not an initial message"
}
```

#### `GET /responded_false`
Handles "No" responses from confirmation buttons (future feature).

**Query Parameters:**
- `user_id` (required) - User UUID
- `conversation_id` (required) - Conversation ID

**Response:**
```json
{
  "status": "response_received_and_transferred",
  "action": "no",
  "conversation_id": 12345,
  "transferred_to_queue": true
}
```

#### `GET /health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy"
}
```

### API Documentation

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## Project Structure

```
dirq/
├── main.py                          # FastAPI application entry point
├── config.py                        # Configuration management (Settings class)
├── requirements.txt                 # Python dependencies
├── railway.json                     # Railway deployment config
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── README.md                        # This file
├── CLAUDE.md                        # Project instructions for Claude Code
├── IMPROVED_PROMPT.md               # OpenAI Prompt template (copy to OpenAI dashboard)
│
├── api/                             # API layer
│   ├── __init__.py
│   ├── dependencies.py              # Service container & dependency injection
│   └── routes/
│       ├── __init__.py
│       ├── webhook.py               # Main webhook handlers
│       └── health.py                # Health check endpoint
│
├── core/                            # Core business logic
│   ├── __init__.py
│   └── services/
│       ├── __init__.py
│       ├── openai_service.py        # OpenAI Prompts API integration
│       ├── formatter_service.py     # Response formatting & HTML buttons
│       ├── dixa_service.py          # Dixa API integration (send messages, transfer)
│       ├── database_service.py      # MongoDB operations (thread-safe singleton)
│       └── validation_service.py    # Email domain & message validation
│
├── models/                          # Pydantic models
│   ├── __init__.py
│   ├── webhook.py                   # Webhook payload models
│   └── conversation.py              # Conversation & message models
│
└── utils/                           # Utilities
    ├── __init__.py
    └── logging.py                   # Logging configuration
```

---

## AI Prompt System

### Prompt Template

The AI uses a comprehensive prompt stored in **IMPROVED_PROMPT.md** and deployed to OpenAI dashboard as version 6.

**Key Characteristics:**
- **Language Detection**: Auto-detects NL, EN, DE, FR, IT
- **Role Detection**: Identifies buyer vs seller from context
- **Intent Classification**: 11 intent categories (refunds, payouts, logistics, etc.)
- **FAQ Search**: Searches Whoppah FAQ database for accurate information
- **Strict Formatting**: Bold text, max 150 words, proper structure
- **9 Handoff Scenarios**: Auto-escalates to humans when needed
- **No False Promises**: Never says "I'll call you" or "I'll arrange this"

### Response Structure

Every AI response follows this exact format:

```
Dear {customerFirstName},

Thank you for your [email/message/question].

[Main answer - 2-3 concise paragraphs with **bold** for key info]

[Optional: ONE FAQ link]

I hope this information is helpful! If you have any further questions, simply reply to this email—we're here to help.

Best regards,
{customerFirstName}
```

### Updating the Prompt

1. Edit `IMPROVED_PROMPT.md` in this repository
2. Copy the entire content
3. Go to OpenAI dashboard → Prompts
4. Update prompt `pmpt_68bcc4524178819485c37da997deecab093b3fe5540d118b`
5. Create new version (increment version number)
6. Update `version` in `core/services/openai_service.py`
7. Deploy to Railway

---

## Idempotency & Duplicate Handling

### Problem

Dixa sends webhooks 2-3 times for the same event, causing:
- Duplicate AI API calls ($$$ waste)
- Duplicate customer emails (bad UX)
- Race conditions in processing

### Solution: Two-Layer Idempotency

**Layer 1: Conversation Collection Check (Fast Path)**
```python
# Check if event_id already exists in conversations
already_processed = db.conversations.find_one({"event_id": event_id})
if already_processed:
    return {"status": "duplicate_ignored"}
```

**Layer 2: Reservation System (Race Condition Protection)**
```python
# Try to insert event_id as unique _id
try:
    db.idempotency.insert_one({"_id": event_id, "reserved_at": now()})
    # Success! Process the event
except DuplicateKeyError:
    # Another request is already processing
    return {"status": "duplicate_ignored"}
```

**Layer 3: TTL Auto-Cleanup**
```python
# Index on reservations collection
db.idempotency.create_index("reserved_at", expireAfterSeconds=300)
# Stale reservations auto-deleted after 5 minutes
```

**Layer 4: Completion Logging**
```python
# After successful processing, log to conversations
db.conversations.insert_one({
    "event_id": event_id,
    "dixa_message_sent": True,
    # ... other fields
})
# Now Layer 1 will catch future duplicates instantly
```

### MongoDB Singleton Pattern

**Problem**: MongoDB was reconnecting on every request (100ms+ latency).

**Solution**: Thread-safe singleton with double-check locking:

```python
class MongoDBService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_connection()
        return cls._instance
```

**Result**: Connection established once, reused for all requests.

---

## Deployment

### Railway Deployment

1. **Install Railway CLI:**
```bash
npm install -g @railway/cli
```

2. **Login and link:**
```bash
railway login
railway link
```

3. **Set environment variables:**
```bash
railway variables --set DIXA_API_KEY=your_key
railway variables --set OPENAI_API_KEY=your_key
railway variables --set MONGODB_URL=mongodb://user:pass@host:port/dirq?authSource=admin
# ... etc
```

4. **Deploy:**
```bash
railway up --service dirq
```

5. **Monitor logs:**
```bash
railway logs --service dirq
```

### Production Configuration

**Railway automatically:**
- Sets `PORT` environment variable
- Handles HTTPS/SSL termination
- Provides health check monitoring
- Auto-deploys on git push to main

**Recommended settings:**
```json
{
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

---

## MCP Integration (Planned)

### Overview

**Goal**: Enable the AI to query real-time Whoppah data (orders, users, payments, listings) via MCP (Model Context Protocol) to provide personalized, accurate responses.

### What is MCP?

MCP (Model Context Protocol) is a protocol that allows AI models to access external data sources and tools through a standardized interface. Think of it as "giving the AI read access to your database" in a safe, controlled way.

### Why MCP for Dirq?

**Current limitation**: AI only has access to static FAQ content.

**With MCP, AI can:**
- Look up order status in real-time
- Check payment status from Stripe
- Verify listing details
- See conversation history
- Check seller payout schedule
- Access user account info

**Example improvement:**

**Before (without MCP):**
```
Customer: "Where is my order #12345?"
AI: "You can track your order in the Whoppah app under 'My Orders'."
```

**After (with MCP):**
```
Customer: "Where is my order #12345?"
AI: "Your order #12345 (Vintage Eames Chair) was shipped via Brenger on Oct 4th
and is scheduled for delivery today between 2-4 PM. The driver will contact you
30 minutes before arrival."
```

### MCP Architecture for Dirq

```
┌─────────────────────────────────────────────────────────────┐
│ Dirq (FastAPI)                                               │
│                                                               │
│  ┌──────────────┐                                            │
│  │ OpenAI       │                                            │
│  │ Prompts API  │                                            │
│  └──────┬───────┘                                            │
│         │                                                     │
│         │ Uses MCP Tools                                     │
│         ▼                                                     │
│  ┌──────────────────────────────────────────────┐           │
│  │ MCP Server (in Dirq)                          │           │
│  │                                                │           │
│  │ Exposes tools:                                 │           │
│  │  - get_order_status(order_id)                 │           │
│  │  - get_payment_status(order_id)               │           │
│  │  - get_listing_details(listing_id)            │           │
│  │  - get_user_info(user_id)                     │           │
│  │  - search_conversations(user_id)              │           │
│  └──────┬───────────────────────────────────────┘           │
│         │                                                     │
└─────────┼─────────────────────────────────────────────────────┘
          │
          │ HTTP/GraphQL Requests
          ▼
┌─────────────────────────────────────────────────────────────┐
│ Whoppah Main Dashboard (Next.js/Django/etc.)                 │
│                                                               │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ PostgreSQL     │  │ Stripe API   │  │ Brenger API  │    │
│  │ (Orders, Users)│  │ (Payments)   │  │ (Shipping)   │    │
│  └────────────────┘  └──────────────┘  └──────────────┘    │
│                                                               │
│  Exposes API endpoints for MCP:                              │
│  - GET /api/mcp/orders/:id                                   │
│  - GET /api/mcp/payments/:id                                 │
│  - GET /api/mcp/listings/:id                                 │
│  - GET /api/mcp/users/:id                                    │
│  - GET /api/mcp/conversations?user_id=...                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Required Components

#### 1. In Main Dashboard (Whoppah Backend)

You need to create API endpoints that Dirq can call:

**File: `pages/api/mcp/orders/[id].ts` (Next.js) or `views/mcp.py` (Django)**

```typescript
// Example Next.js API route
export default async function handler(req, res) {
  const { id } = req.query;

  // Verify API key from Dirq
  if (req.headers.authorization !== `Bearer ${process.env.MCP_API_KEY}`) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  // Fetch order from database
  const order = await prisma.order.findUnique({
    where: { id: parseInt(id) },
    include: {
      buyer: true,
      seller: true,
      listing: true,
      shipping: true,
      payment: true
    }
  });

  if (!order) {
    return res.status(404).json({ error: 'Order not found' });
  }

  // Return sanitized order data
  return res.json({
    id: order.id,
    status: order.status, // e.g., 'shipped', 'delivered', 'pending'
    listing: {
      title: order.listing.title,
      price: order.listing.price
    },
    buyer: {
      name: order.buyer.firstName,
      email: order.buyer.email
    },
    seller: {
      name: order.seller.firstName,
      email: order.seller.email
    },
    shipping: {
      method: order.shipping.method, // 'brenger', 'postal', 'pickup'
      trackingCode: order.shipping.trackingCode,
      estimatedDelivery: order.shipping.estimatedDelivery,
      status: order.shipping.status
    },
    payment: {
      status: order.payment.status, // 'paid', 'pending', 'refunded'
      paidAt: order.payment.paidAt,
      method: order.payment.method
    },
    timeline: [
      { event: 'Order placed', timestamp: order.createdAt },
      { event: 'Payment received', timestamp: order.payment.paidAt },
      { event: 'Shipped', timestamp: order.shipping.shippedAt },
      // ...
    ]
  });
}
```

**Required MCP API Endpoints in Main Dashboard:**

```
GET  /api/mcp/orders/:id              - Get order details & status
GET  /api/mcp/orders/user/:userId     - Get all orders for a user
GET  /api/mcp/payments/:orderId       - Get payment status & details
GET  /api/mcp/listings/:id            - Get listing details
GET  /api/mcp/users/:id               - Get user account info
GET  /api/mcp/conversations/:userId   - Get conversation history
GET  /api/mcp/shipping/:orderId       - Get shipping/tracking info
POST /api/mcp/search                  - Search across orders/listings
```

**Authentication:**
- Use API key authentication (Bearer token)
- Generate a secure API key for Dirq
- Store in Dirq's environment variables as `MCP_API_KEY`

#### 2. In Dirq (This Project)

Create MCP client that calls the main dashboard APIs:

**File: `core/services/mcp_service.py`**

```python
import httpx
from config import settings

class MCPService:
    """
    MCP (Model Context Protocol) client for querying Whoppah data
    Connects to main dashboard API endpoints
    """

    def __init__(self):
        self.base_url = settings.MCP_BASE_URL  # e.g., https://dashboard.whoppah.com
        self.api_key = settings.MCP_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def get_order_status(self, order_id: int) -> dict:
        """Get order status and details"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/mcp/orders/{order_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_user_orders(self, user_id: str) -> list:
        """Get all orders for a user"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/mcp/orders/user/{user_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_payment_status(self, order_id: int) -> dict:
        """Get payment status for an order"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/mcp/payments/{order_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    # ... more MCP tool methods
```

#### 3. OpenAI Prompt Update

Update `IMPROVED_PROMPT.md` to include MCP tools:

```markdown
## Available MCP Tools

You have access to real-time Whoppah data through these tools:

### get_order_status(order_id: int)
Returns current status, shipping info, and timeline for an order.

**When to use:**
- Customer asks about order status
- Customer mentions an order number
- Questions about delivery/tracking

**Example:**
```
Customer: "Where is my order #12345?"
You: [Call get_order_status(12345)]
Response: "Your order #12345 (Vintage Eames Chair) shipped via Brenger on Oct 4th..."
```

### get_payment_status(order_id: int)
Returns payment status and refund info.

**When to use:**
- Payment questions
- Refund status inquiries
- Payout questions (for sellers)

... (document all MCP tools)
```

### Implementation Steps

**Phase 1: Main Dashboard API (Week 1)**
1. Create `/api/mcp/` directory in main dashboard
2. Implement `orders/:id` endpoint
3. Implement `payments/:id` endpoint
4. Add API key authentication
5. Test endpoints with Postman/curl

**Phase 2: Dirq MCP Client (Week 2)**
1. Create `core/services/mcp_service.py`
2. Implement MCP tool methods
3. Add error handling & retries
4. Add caching for frequently accessed data
5. Add logging & monitoring

**Phase 3: OpenAI Integration (Week 3)**
1. Update OpenAI Prompt with MCP tools
2. Configure OpenAI to use MCP tools
3. Test with sample customer queries
4. Monitor API usage & costs

**Phase 4: Production Rollout (Week 4)**
1. Deploy to staging environment
2. A/B test with/without MCP
3. Monitor response quality
4. Gradual rollout to production

### Security Considerations

**API Key Management:**
- Generate secure API key (min 32 chars)
- Rotate keys quarterly
- Store in Railway secrets, never in code
- Use different keys for staging/production

**Data Privacy:**
- Only expose minimal necessary data
- Sanitize PII (hide full email, show first name only)
- Don't expose payment card details
- Log all MCP API calls for audit

**Rate Limiting:**
- Limit Dirq to 100 req/min per endpoint
- Implement exponential backoff
- Cache responses (30-60 sec TTL)
- Alert on unusual patterns

### Cost Estimation

**MCP API Calls:**
- Average: 2-3 MCP calls per customer question
- ~1000 customer emails/day
- = 2000-3000 API calls/day
- Negligible cost (internal API calls)

**OpenAI with MCP:**
- MCP tools increase token usage by ~30%
- Current: $0.05/request → With MCP: $0.065/request
- 1000 requests/day = $50/day → $65/day
- Extra cost: $15/day = $450/month
- **ROI**: Saves 10+ hours of human support/day = $2000/month

---

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/

# Run with coverage
pytest --cov=core --cov=api tests/
```

### Code Style

- **PEP 8** compliance
- **Type hints** for all function signatures
- **Docstrings** for all classes and public methods
- **Async/await** for I/O operations
- **Logging** for all important events

### Adding a New Feature

1. Create feature branch: `git checkout -b feature/your-feature`
2. Implement feature with tests
3. Update this README if needed
4. Create pull request
5. Deploy to staging for testing
6. Merge to main → auto-deploys to production

---

## Monitoring & Debugging

### Logs

All logs are structured with emojis for easy scanning:

```
🔔 WEBHOOK RECEIVED
🔐 Attempting to acquire reservation
✅ Reservation acquired
⏰ TIMESTAMP PROCESSING
🔍 VALIDATION PROCESSING
🤖 AI PROCESSING STARTED
📤 DIXA MESSAGE SENDING
💾 DATABASE LOGGING
🎉 WEBHOOK PROCESSING COMPLETED
```

**Error logs:**
```
❌ Failed to connect to MongoDB
⚠️ Duplicate detected
💥 WEBHOOK ERROR - Unexpected exception
```

### Railway Logs

```bash
# Tail logs in real-time
railway logs --service dirq

# Filter for errors only
railway logs --service dirq | grep "ERROR"

# Check MongoDB connection
railway logs --service dirq | grep "MongoDB"
```

### Health Checks

```bash
# Manual health check
curl https://dirq-production.up.railway.app/health

# Automated monitoring (Railway)
# Health check path: /health
# Timeout: 300s
```

### Common Issues

**Issue: MongoDB reconnecting on every request**
- **Cause**: Singleton not working
- **Fix**: Check `MongoDBService._instance` is set
- **Log**: Should see "Creating new MongoDBService singleton instance" only ONCE

**Issue: Duplicate webhooks still processing**
- **Cause**: Race condition in idempotency check
- **Fix**: Check `idempotency` collection has unique index on `_id`
- **Log**: Should see "⚠️ Duplicate detected" for concurrent requests

**Issue: AI returning error messages**
- **Cause**: Prompt variables mismatch or OpenAI API error
- **Fix**: Check `prompt.variables` matches OpenAI prompt template
- **Log**: Look for "OpenAI Prompts API error" with stack trace

---

## License

Proprietary - Whoppah B.V.

---

## Contributing

This is an internal Whoppah project. For questions or contributions, contact the engineering team.

---

**Last Updated**: 2025-10-06
**Version**: 1.0.0
**Maintained by**: Whoppah Engineering Team
