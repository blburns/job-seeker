# API Documentation

## Overview

This application provides a RESTful API alongside the web interface. The API is built using Flask-RESTX and follows RESTful principles.

## Base URL

```
http://localhost:5000/api/v1
```

## Authentication

Most API endpoints require authentication. Use one of these methods:

### 1. Session Authentication (Web)

If accessing from the same browser session:
- Cookies are automatically sent
- No additional headers needed

### 2. JWT Authentication (API Clients)

```http
Authorization: Bearer <access_token>
```

**Get Access Token:**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_in": 3600
}
```

### 3. API Key (if implemented)

```http
X-API-Key: your-api-key
```

## Common Headers

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <token>
```

## Response Format

### Success Response

```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response

```json
{
  "status": "error",
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

### Pagination Response

```json
{
  "status": "success",
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  }
}
```

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## Rate Limiting

API endpoints are rate-limited:

- **Default:** 10,000 requests/hour, 1,000 requests/minute
- **Headers:** Rate limit info in response headers
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## Endpoints

### Health Check

**GET** `/api/v1/health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T12:00:00Z",
  "version": "1.0.0"
}
```

### Authentication Endpoints

#### Login

**POST** `/api/v1/auth/login`

Authenticate and get access token.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "username": "user",
    "email": "user@example.com"
  }
}
```

#### Refresh Token

**POST** `/api/v1/auth/refresh`

Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_in": 3600
}
```

#### Logout

**POST** `/api/v1/auth/logout`

Invalidate tokens.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```

### User Endpoints

#### List Users

**GET** `/api/v1/users`

List all users (paginated).

**Query Parameters:**
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)
- `search` - Search term
- `role` - Filter by role
- `is_active` - Filter by active status

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "username": "user",
      "email": "user@example.com",
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  }
}
```

#### Get User

**GET** `/api/v1/users/<user_id>`

Get user details.

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "username": "user",
    "email": "user@example.com",
    "firstname": "John",
    "lastname": "Doe",
    "is_active": true,
    "roles": ["user", "manager"],
    "groups": ["sales"],
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

#### Create User

**POST** `/api/v1/users`

Create new user.

**Request:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "secure-password",
  "firstname": "Jane",
  "lastname": "Smith",
  "roles": ["user"]
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "username": "newuser",
    "email": "newuser@example.com"
  },
  "message": "User created successfully"
}
```

#### Update User

**PUT** `/api/v1/users/<user_id>`

Update user.

**Request:**
```json
{
  "firstname": "Jane",
  "lastname": "Doe",
  "is_active": true
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "username": "user",
    "firstname": "Jane",
    "lastname": "Doe"
  }
}
```

#### Delete User

**DELETE** `/api/v1/users/<user_id>`

Delete user (soft delete).

**Response:**
```json
{
  "status": "success",
  "message": "User deleted successfully"
}
```

### Account Endpoints

#### List Accounts

**GET** `/api/v1/accounts`

List all accounts.

**Query Parameters:**
- `page` - Page number
- `per_page` - Items per page
- `status` - Filter by status
- `account_type` - Filter by type
- `search` - Search term

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "account_uuid": "uuid",
      "account_name": "Acme Corp",
      "account_number": "ACC001",
      "status": "active",
      "primary_email": "contact@acme.com"
    }
  ]
}
```

#### Get Account

**GET** `/api/v1/accounts/<account_uuid>`

Get account details.

#### Create Account

**POST** `/api/v1/accounts`

Create new account.

**Request:**
```json
{
  "account_name": "New Company",
  "account_number": "ACC002",
  "account_type_id": "uuid",
  "primary_email": "contact@newcompany.com",
  "status": "active"
}
```

#### Update Account

**PUT** `/api/v1/accounts/<account_uuid>`

Update account.

#### Delete Account

**DELETE** `/api/v1/accounts/<account_uuid>`

Delete account.

## Error Handling

### Validation Errors

**Status:** `422`

```json
{
  "status": "error",
  "error": "Validation failed",
  "errors": {
    "email": ["Invalid email format"],
    "password": ["Password must be at least 8 characters"]
  }
}
```

### Permission Denied

**Status:** `403`

```json
{
  "status": "error",
  "error": "Permission denied",
  "code": "PERMISSION_DENIED"
}
```

### Not Found

**Status:** `404`

```json
{
  "status": "error",
  "error": "Resource not found",
  "code": "NOT_FOUND"
}
```

## API Client Examples

### Python (requests)

```python
import requests

base_url = "http://localhost:5000/api/v1"

# Login
response = requests.post(f"{base_url}/auth/login", json={
    "username": "user@example.com",
    "password": "password"
})
token = response.json()["access_token"]

# Get users
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{base_url}/users", headers=headers)
users = response.json()["data"]
```

### JavaScript (fetch)

```javascript
const baseUrl = 'http://localhost:5000/api/v1';

// Login
const loginResponse = await fetch(`${baseUrl}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user@example.com',
    password: 'password'
  })
});
const { access_token } = await loginResponse.json();

// Get users
const usersResponse = await fetch(`${baseUrl}/users`, {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const { data: users } = await usersResponse.json();
```

### cURL

```bash
# Login
TOKEN=$(curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

# Get users
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/v1/users
```

## API Versioning

The API uses URL versioning:
- Current version: `v1`
- Future versions: `v2`, `v3`, etc.

## CORS Configuration

CORS is enabled for API endpoints. Configure allowed origins in `.env`:

```env
CORS_ORIGINS=http://localhost:3000,https://yourapp.com
```

## Webhooks (Future)

Webhook support may be added for:
- User created/updated
- Account created/updated
- Document uploaded
- etc.

## See Also

- [RBAC_GUIDE.md](RBAC_GUIDE.md) - Permission system
- [MODULE_DEVELOPMENT.md](MODULE_DEVELOPMENT.md) - Adding API endpoints
