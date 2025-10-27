# Whoppah User Context API - Complete Documentation

## 📋 Overview

REST API endpoint that returns complete user context including profile, order history, and message threads.

**Base URL:** `https://dashboard.production.whoppah.com`

**Endpoint:** `/api/v1/thirdparty/dixa/mcp/user-context/`

**Method:** `GET`

**Authentication:** Token-based

---

## 🔐 Authentication

### Header Required

```http
Authorization: Token YOUR_API_TOKEN_HERE
```

### Getting a Token

```bash
# On production server
python manage.py drf_create_token openai_user_context
```

---

## 📥 Request

### URL Structure

```
GET https://dashboard.production.whoppah.com/api/v1/thirdparty/dixa/mcp/user-context/?email={email}&orders_limit={limit}&threads_limit={limit}
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `email` | string | ✅ **Yes** | - | User's email address (case-sensitive) |
| `orders_limit` | integer | ❌ No | 5 | Number of recent orders to return (max recommended: 20) |
| `threads_limit` | integer | ❌ No | 3 | Number of recent message threads to return (max recommended: 10) |

### Example Requests

**Basic request:**
```bash
curl -X GET \
  -H "Authorization: Token YOUR_TOKEN" \
  "https://dashboard.production.whoppah.com/api/v1/thirdparty/dixa/mcp/user-context/?email=omer@whoppah.com"
```

**With custom limits:**
```bash
curl -X GET \
  -H "Authorization: Token YOUR_TOKEN" \
  "https://dashboard.production.whoppah.com/api/v1/thirdparty/dixa/mcp/user-context/?email=omer@whoppah.com&orders_limit=10&threads_limit=5"
```

---

## 📤 Response

### Success Response (200 OK)

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "omer@whoppah.com",
  "name": "Omer Example",
  "user_type": "business",
  "phone": "+31612345678",
  "created_at": "2023-01-15T10:30:00+00:00",
  "total_order_value": 1250.50,
  "total_orders_count": 15,
  "stripe_account_active": true,
  "stripe_customer_active": true,
  "recent_orders": [...],
  "recent_threads": [...],
  "stats": {...}
}
```

---

## 📊 Response Fields

### Root Level Fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `user_id` | string (UUID) | No | Unique user identifier |
| `email` | string | No | User's email address |
| `name` | string | No | User's full name |
| `user_type` | string | No | Account type: `"business"`, `"individual"`, etc. |
| `phone` | string | Yes | Phone number in international format (e.g., "+31612345678") |
| `created_at` | string (ISO 8601) | Yes | Account creation timestamp in UTC |
| `total_order_value` | number (float) | No | Total value of all completed orders in EUR |
| `total_orders_count` | integer | No | Total number of orders (as buyer or seller) |
| `stripe_account_active` | boolean | No | Whether user has active Stripe seller account |
| `stripe_customer_active` | boolean | No | Whether user has active Stripe customer account |
| `recent_orders` | array | No | Array of recent order objects (see below) |
| `recent_threads` | array | No | Array of recent message thread objects (see below) |
| `stats` | object | No | Summary statistics object (see below) |

---

## 🛒 Order Object Structure

Each object in `recent_orders` array:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "identifier": "WH-2024-001",
  "role": "buyer",
  "state": "shipped",
  "product_title": "Vintage Leather Chair",
  "product_id": "650e8400-e29b-41d4-a716-446655440001",
  "amount": 150.00,
  "total": 165.00,
  "payout": null,
  "created_at": "2024-10-01T14:30:00+00:00",
  "delivery_method": "delivery",
  "delivery_method_display": "Delivery",
  "shipping_method": "Brenger",
  "outsource_shipping_method": "brenger",
  "buyer_name": "Omer Example",
  "seller_name": "Jane Smith",
  "refund_reason": null,
  "return_status": null
}
```

### Order Fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | string (UUID) | No | Unique order identifier |
| `identifier` | string | No | Human-readable order number (e.g., "WH-2024-001") |
| `role` | string | No | User's role in this order: `"buyer"` or `"seller"` |
| `state` | string | No | Order status (see Order States below) |
| `product_title` | string | Yes | Product name/title |
| `product_id` | string (UUID) | No | Product identifier |
| `amount` | number (float) | No | Subtotal amount in EUR (excluding fees) |
| `total` | number (float) | No | Total amount in EUR (including all fees) |
| `payout` | number (float) | Yes | Seller payout amount in EUR (null for buyers) |
| `created_at` | string (ISO 8601) | Yes | Order creation timestamp in UTC |
| `delivery_method` | string | No | Delivery method code (see Delivery Methods below) |
| `delivery_method_display` | string | No | Human-readable delivery method |
| `shipping_method` | string | Yes | Shipping provider name (e.g., "Brenger", "PostNL") |
| `outsource_shipping_method` | string | Yes | Outsourced shipping method identifier |
| `buyer_name` | string | Yes | Buyer's full name |
| `seller_name` | string | Yes | Seller's full name |
| `refund_reason` | string | Yes | Reason for refund if applicable |
| `return_status` | string | Yes | Return status if applicable |

### Order States

Possible values for `state` field:

| State | Description |
|-------|-------------|
| `"new"` | Order just created, awaiting payment |
| `"accepted"` | Payment received, order confirmed |
| `"shipped"` | Order has been shipped |
| `"delivered"` | Order delivered to buyer |
| `"completed"` | Order fully completed |
| `"canceled"` | Order canceled |
| `"expired"` | Order expired (payment not received) |
| `"refunded"` | Order refunded |

### Delivery Methods

Possible values for `delivery_method` field:

| Code | Display Name | Description |
|------|--------------|-------------|
| `"pickup"` | "Self-pickup" | Buyer picks up from seller |
| `"delivery"` | "Delivery" | Delivery service used |
| `"postal"` | "Postal service" | Sent via postal service |

---

## 💬 Thread Object Structure

Each object in `recent_threads` array:

```json
{
  "id": "750e8400-e29b-41d4-a716-446655440002",
  "identifier": "TH-2024-001",
  "object_id": "850e8400-e29b-41d4-a716-446655440003",
  "product_title": "Vintage Leather Chair",
  "other_user": {
    "name": "Jane Smith",
    "email": "jane@example.com"
  },
  "last_message": {
    "text": "When can you deliver the chair?",
    "created_at": "2024-10-05T09:15:00+00:00"
  },
  "created_at": "2024-10-01T14:00:00+00:00",
  "updated_at": "2024-10-05T09:15:00+00:00"
}
```

### Thread Fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | string (UUID) | No | Unique thread identifier |
| `identifier` | string | No | Human-readable thread number (e.g., "TH-2024-001") |
| `object_id` | string (UUID) | No | Related object ID (usually product ID) |
| `product_title` | string | Yes | Related product title |
| `other_user` | object | Yes | Other participant in conversation (see below) |
| `last_message` | object | Yes | Most recent message in thread (see below) |
| `created_at` | string (ISO 8601) | Yes | Thread creation timestamp in UTC |
| `updated_at` | string (ISO 8601) | Yes | Last update timestamp in UTC |

### Other User Object

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Other user's full name |
| `email` | string | Other user's email address |

### Last Message Object

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Message content (truncated to 200 characters) |
| `created_at` | string (ISO 8601) | Message timestamp in UTC |

---

## 📈 Stats Object Structure

```json
{
  "buyer_orders": 10,
  "seller_orders": 5,
  "orders_by_state": {
    "completed": 8,
    "shipped": 2,
    "accepted": 3,
    "canceled": 2
  },
  "has_active_orders": true,
  "has_pending_issues": false
}
```

### Stats Fields

| Field | Type | Description |
|-------|------|-------------|
| `buyer_orders` | integer | Number of orders where user is buyer (from recent_orders) |
| `seller_orders` | integer | Number of orders where user is seller (from recent_orders) |
| `orders_by_state` | object | Count of orders grouped by state |
| `has_active_orders` | boolean | True if user has orders in "accepted" or "shipped" state |
| `has_pending_issues` | boolean | True if any order has refund_reason or return_status |

---

## ❌ Error Responses

### 400 Bad Request - Missing Email

```json
{
  "error": "email parameter is required"
}
```

**Cause:** Email query parameter not provided

---

### 401 Unauthorized - Invalid Token

```json
{
  "detail": "Invalid token."
}
```

**Cause:** Missing or invalid Authorization header

---

### 404 Not Found - User Not Found

```json
{
  "error": "User not found"
}
```

**Cause:** No user exists with the provided email address

---

### 500 Internal Server Error

```json
{
  "error": "Internal server error: <error message>"
}
```

**Cause:** Server-side error (database connection, etc.)

---

## 💻 Client Code Examples

### Python

```python
import requests

def get_user_context(email, orders_limit=5, threads_limit=3):
    """
    Fetch user context from Whoppah API
    
    Args:
        email: User's email address
        orders_limit: Number of recent orders (default: 5)
        threads_limit: Number of recent threads (default: 3)
    
    Returns:
        dict: User context data
    
    Raises:
        requests.HTTPError: If request fails
    """
    url = "https://dashboard.production.whoppah.com/api/v1/thirdparty/dixa/mcp/user-context/"
    
    headers = {
        "Authorization": "Token YOUR_API_TOKEN_HERE",
        "Content-Type": "application/json"
    }
    
    params = {
        "email": email,
        "orders_limit": orders_limit,
        "threads_limit": threads_limit
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise exception for 4xx/5xx status codes
    
    return response.json()


# Usage
try:
    user_data = get_user_context("omer@whoppah.com", orders_limit=10)
    
    print(f"User: {user_data['name']}")
    print(f"Total Orders: {user_data['total_orders_count']}")
    print(f"Total Value: €{user_data['total_order_value']}")
    
    # Access recent orders
    for order in user_data['recent_orders']:
        print(f"Order {order['identifier']}: {order['state']} - €{order['total']}")
    
    # Access recent threads
    for thread in user_data['recent_threads']:
        if thread['last_message']:
            print(f"Thread with {thread['other_user']['name']}: {thread['last_message']['text']}")
    
except requests.HTTPError as e:
    print(f"Error: {e}")
    print(f"Response: {e.response.text}")
```

---

### JavaScript/Node.js

```javascript
const axios = require('axios');

/**
 * Fetch user context from Whoppah API
 * @param {string} email - User's email address
 * @param {number} ordersLimit - Number of recent orders (default: 5)
 * @param {number} threadsLimit - Number of recent threads (default: 3)
 * @returns {Promise<Object>} User context data
 */
async function getUserContext(email, ordersLimit = 5, threadsLimit = 3) {
  const url = 'https://dashboard.production.whoppah.com/api/v1/thirdparty/dixa/mcp/user-context/';
  
  try {
    const response = await axios.get(url, {
      headers: {
        'Authorization': 'Token YOUR_API_TOKEN_HERE',
        'Content-Type': 'application/json'
      },
      params: {
        email: email,
        orders_limit: ordersLimit,
        threads_limit: threadsLimit
      }
    });
    
    return response.data;
  } catch (error) {
    if (error.response) {
      // Server responded with error status
      console.error('Error:', error.response.status, error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('No response received:', error.request);
    } else {
      // Error setting up request
      console.error('Error:', error.message);
    }
    throw error;
  }
}

// Usage
(async () => {
  try {
    const userData = await getUserContext('omer@whoppah.com', 10, 5);
    
    console.log(`User: ${userData.name}`);
    console.log(`Total Orders: ${userData.total_orders_count}`);
    console.log(`Total Value: €${userData.total_order_value}`);
    
    // Access recent orders
    userData.recent_orders.forEach(order => {
      console.log(`Order ${order.identifier}: ${order.state} - €${order.total}`);
    });
    
    // Access recent threads
    userData.recent_threads.forEach(thread => {
      if (thread.last_message) {
        console.log(`Thread with ${thread.other_user.name}: ${thread.last_message.text}`);
      }
    });
    
  } catch (error) {
    console.error('Failed to fetch user context');
  }
})();
```

---

### TypeScript

```typescript
interface UserContext {
  user_id: string;
  email: string;
  name: string;
  user_type: string;
  phone: string | null;
  created_at: string | null;
  total_order_value: number;
  total_orders_count: number;
  stripe_account_active: boolean;
  stripe_customer_active: boolean;
  recent_orders: Order[];
  recent_threads: Thread[];
  stats: Stats;
}

interface Order {
  id: string;
  identifier: string;
  role: 'buyer' | 'seller';
  state: string;
  product_title: string | null;
  product_id: string;
  amount: number;
  total: number;
  payout: number | null;
  created_at: string | null;
  delivery_method: string;
  delivery_method_display: string;
  shipping_method: string | null;
  outsource_shipping_method: string | null;
  buyer_name: string | null;
  seller_name: string | null;
  refund_reason: string | null;
  return_status: string | null;
}

interface Thread {
  id: string;
  identifier: string;
  object_id: string;
  product_title: string | null;
  other_user: {
    name: string;
    email: string;
  } | null;
  last_message: {
    text: string;
    created_at: string;
  } | null;
  created_at: string | null;
  updated_at: string | null;
}

interface Stats {
  buyer_orders: number;
  seller_orders: number;
  orders_by_state: Record<string, number>;
  has_active_orders: boolean;
  has_pending_issues: boolean;
}

async function getUserContext(
  email: string,
  ordersLimit: number = 5,
  threadsLimit: number = 3
): Promise<UserContext> {
  const url = 'https://dashboard.production.whoppah.com/api/v1/thirdparty/dixa/mcp/user-context/';
  
  const response = await fetch(
    `${url}?email=${encodeURIComponent(email)}&orders_limit=${ordersLimit}&threads_limit=${threadsLimit}`,
    {
      headers: {
        'Authorization': 'Token YOUR_API_TOKEN_HERE',
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(`API Error: ${error.error || response.statusText}`);
  }
  
  return response.json();
}

// Usage
getUserContext('omer@whoppah.com', 10, 5)
  .then(userData => {
    console.log(`User: ${userData.name}`);
    console.log(`Total Orders: ${userData.total_orders_count}`);
    
    userData.recent_orders.forEach(order => {
      console.log(`Order ${order.identifier}: ${order.state}`);
    });
  })
  .catch(error => {
    console.error('Error:', error.message);
  });
```

---

### cURL

```bash
# Basic request
curl -X GET \
  -H "Authorization: Token YOUR_API_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  "https://dashboard.production.whoppah.com/api/v1/thirdparty/dixa/mcp/user-context/?email=omer@whoppah.com"

# With custom limits
curl -X GET \
  -H "Authorization: Token YOUR_API_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  "https://dashboard.production.whoppah.com/api/v1/thirdparty/dixa/mcp/user-context/?email=omer@whoppah.com&orders_limit=10&threads_limit=5"

# Pretty print with jq
curl -X GET \
  -H "Authorization: Token YOUR_API_TOKEN_HERE" \
  "https://dashboard.production.whoppah.com/api/v1/thirdparty/dixa/mcp/user-context/?email=omer@whoppah.com" | jq
```

---

## 🔍 Use Cases

### 1. Customer Support Context

```python
# Get customer's recent activity for support agent
user_data = get_user_context("customer@example.com")

# Check for active orders
if user_data['stats']['has_active_orders']:
    print("Customer has active orders in progress")

# Check for issues
if user_data['stats']['has_pending_issues']:
    print("⚠️ Customer has pending refunds or returns")

# Show recent orders
for order in user_data['recent_orders']:
    if order['role'] == 'buyer':
        print(f"Bought: {order['product_title']} - Status: {order['state']}")
```

### 2. AI Assistant Context

```python
# Provide context to AI for personalized responses
user_data = get_user_context("customer@example.com", orders_limit=3)

context = f"""
User: {user_data['name']}
Total Orders: {user_data['total_orders_count']}
Recent Orders:
"""

for order in user_data['recent_orders']:
    context += f"- {order['identifier']}: {order['product_title']} ({order['state']})\n"

# Feed context to AI model
ai_response = generate_ai_response(user_query, context)
```

### 3. Order Status Lookup

```python
# Find specific order by identifier
user_data = get_user_context("customer@example.com", orders_limit=20)

order_number = "WH-2024-001"
order = next((o for o in user_data['recent_orders'] if o['identifier'] == order_number), None)

if order:
    print(f"Order {order_number} status: {order['state']}")
    print(f"Delivery: {order['delivery_method_display']}")
    if order['shipping_method']:
        print(f"Shipping: {order['shipping_method']}")
else:
    print(f"Order {order_number} not found in recent orders")
```

---

## ⚡ Performance

### Response Times

- **Average**: 300-500ms
- **User lookup**: ~50ms
- **Order queries**: ~100-200ms
- **Thread queries**: ~100-150ms

### Optimization Tips

1. **Use appropriate limits**: Don't request more data than needed
   - Default limits (5 orders, 3 threads) are optimized for most use cases
   - Higher limits increase response time

2. **Cache responses**: Cache user context for short periods (30-60 seconds)
   - Reduces API calls
   - Improves response time for repeated requests

3. **Parallel requests**: If fetching multiple users, use async/parallel requests

---

## 🔒 Security

### Best Practices

1. **Store token securely**: Never commit tokens to version control
2. **Use environment variables**: Store token in `.env` file
3. **HTTPS only**: Always use HTTPS in production
4. **Rate limiting**: Implement client-side rate limiting
5. **Error handling**: Handle all error responses gracefully

### Token Security

```python
# ✅ Good: Use environment variables
import os
TOKEN = os.getenv('WHOPPAH_API_TOKEN')

# ❌ Bad: Hardcoded token
TOKEN = "1163a9ca3473b260e90e92c259090c37fd87c3af"
```

---

## 📞 Support

For issues or questions:
- Check error response messages
- Verify token is valid
- Ensure email parameter is correct
- Check network connectivity
- Review logs for detailed error information

---

## 📝 Changelog

### Version 1.0.0 (Current)
- Initial release
- User profile fields
- Order history with full details
- Message threads with participants
- Summary statistics
- Token authentication

---

**Last Updated:** 2025-10-09
**API Version:** 1.0.0
**Base URL:** `https://dashboard.production.whoppah.com`
