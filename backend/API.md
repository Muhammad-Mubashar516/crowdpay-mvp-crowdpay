# CrowdPay API Documentation

Base URL: `http://localhost:5000` (development) or your production domain

**Payment Provider**: LNbits (Lightning Network only)

## Table of Contents
- [Authentication](#authentication)
- [Health Check](#health-check)
- [Campaigns](#campaigns)
- [Contributions](#contributions)
- [Invoices & Wallet](#invoices--wallet)
- [Webhooks](#webhooks)
- [Error Responses](#error-responses)

## Authentication

The API uses LNbits API keys for payment operations. The backend handles all LNbits communication - **frontend never sees admin keys**.

For protected endpoints, use Bearer token authentication:
```http
Authorization: Bearer <your-jwt-token>
```

## Health Check

### Check API Health
```http
GET /health
```

**Response** (200 OK)
```json
{
  "status": "healthy",
  "service": "CrowdPay API",
  "version": "2.0.0",
  "payment_provider": "LNbits"
}
```

### Check Payments Health
```http
GET /api/health
```

**Response** (200 OK)
```json
{
  "status": "healthy",
  "lnbits_connected": true,
  "wallet_id": "abc123...",
  "balance_sats": 100000
}
```

## Campaigns

### Create Campaign

Create a new fundraising campaign.

```http
POST /api/campaigns
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body**
```json
{
  "title": "Community Event Fundraiser",
  "description": "Help us organize an amazing community event",
  "target_amount": 1000000,
  "currency": "SATS",
  "creator_id": "user_123",
  "creator_email": "creator@example.com",
  "end_date": "2025-12-31T23:59:59Z"
}
```

**Response** (201 Created)
```json
{
  "message": "Campaign created successfully",
  "campaign": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Community Event Fundraiser",
    "description": "Help us organize an amazing community event",
    "target_amount": 1000000,
    "current_amount": 0,
    "currency": "SATS",
    "creator_id": "user_123",
    "status": "active",
    "created_at": "2025-01-07T10:30:00Z"
  }
}
```

### List Campaigns

```http
GET /api/campaigns?status=active&limit=10&offset=0
```

**Query Parameters**
- `status` (optional) - Filter by status: `active`, `completed`, `cancelled`, `expired`
- `creator_id` (optional) - Filter by creator
- `limit` (optional) - Results per page (default: 50)
- `offset` (optional) - Pagination offset (default: 0)

**Response** (200 OK)
```json
{
  "campaigns": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Community Event Fundraiser",
      "target_amount": 1000000,
      "current_amount": 500000,
      "status": "active"
    }
  ],
  "count": 1,
  "offset": 0,
  "limit": 10
}
```

### Get Campaign Details

```http
GET /api/campaigns/{campaign_id}
```

**Response** (200 OK)
```json
{
  "campaign": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Community Event Fundraiser",
    "description": "Help us organize an amazing community event",
    "target_amount": 1000000,
    "current_amount": 500000,
    "currency": "SATS",
    "creator_id": "user_123",
    "status": "active",
    "created_at": "2025-01-07T10:30:00Z"
  },
  "statistics": {
    "progress_percentage": 50.0,
    "remaining_amount": 500000,
    "total_contributions": 25,
    "paid_contributions": 20,
    "is_goal_reached": false
  }
}
```

### Update Campaign

```http
PUT /api/campaigns/{campaign_id}
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body**
```json
{
  "title": "Updated Campaign Title",
  "description": "Updated description",
  "target_amount": 1500000
}
```

### Delete Campaign

```http
DELETE /api/campaigns/{campaign_id}
Authorization: Bearer <token>
```

## Contributions

### Create Contribution

Create a new contribution and generate a Lightning invoice.

```http
POST /api/contributions
Content-Type: application/json
```

**Request Body**
```json
{
  "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
  "contributor_name": "John Doe",
  "contributor_email": "john@example.com",
  "amount": 10000,
  "currency": "SATS",
  "message": "Happy to support this cause!",
  "is_anonymous": false
}
```

**Response** (201 Created)
```json
{
  "message": "Contribution created successfully",
  "contribution": {
    "id": "contrib_123",
    "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
    "contributor_name": "John Doe",
    "amount": 10000,
    "currency": "SATS",
    "payment_status": "pending",
    "created_at": "2025-01-07T10:45:00Z"
  },
  "payment_request": "lnbc100n1pj...",
  "payment_hash": "abc123def456..."
}
```

The `payment_request` is a BOLT11 Lightning invoice string. Display this as a QR code for the user to scan with their Lightning wallet.

### Get Contribution Details

```http
GET /api/contributions/{contribution_id}
```

**Response** (200 OK)
```json
{
  "contribution": {
    "id": "contrib_123",
    "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
    "contributor_name": "John Doe",
    "amount": 10000,
    "currency": "SATS",
    "payment_status": "paid",
    "paid_at": "2025-01-07T10:50:00Z",
    "transaction_id": "preimage_abc123",
    "message": "Happy to support this cause!",
    "created_at": "2025-01-07T10:45:00Z"
  }
}
```

### Check Payment Status

Poll this endpoint to check if payment has been received.

```http
GET /api/contributions/{contribution_id}/status
```

**Response** (200 OK)
```json
{
  "contribution_id": "contrib_123",
  "payment_status": "paid",
  "is_paid": true,
  "paid_at": "2025-01-07T10:50:00Z"
}
```

**Payment Status Values:**
- `pending` - Awaiting payment
- `paid` - Payment confirmed
- `failed` - Payment failed
- `expired` - Invoice expired
- `cancelled` - Contribution cancelled

### Cancel Contribution

```http
POST /api/contributions/{contribution_id}/cancel
Authorization: Bearer <token>
```

**Response** (200 OK)
```json
{
  "message": "Contribution cancelled successfully"
}
```

### List Contributions

```http
GET /api/contributions?campaign_id=550e8400...&payment_status=paid&limit=20
```

**Query Parameters**
- `campaign_id` (optional) - Filter by campaign
- `payment_status` (optional) - Filter by status
- `limit` (optional) - Results per page (default: 50)
- `offset` (optional) - Pagination offset (default: 0)

## Invoices & Wallet

### Create Standalone Invoice

Create a Lightning invoice without a contribution record (for testing).

```http
POST /api/invoice/create
Content-Type: application/json
```

**Request Body**
```json
{
  "amount": 1000,
  "memo": "Test payment",
  "expiry": 3600
}
```

**Response** (201 Created)
```json
{
  "payment_hash": "abc123...",
  "payment_request": "lnbc10n1pj...",
  "amount": 1000,
  "memo": "Test payment",
  "expiry": 3600
}
```

### Check Invoice Status

```http
GET /api/invoice/status/{payment_hash}
```

**Response** (200 OK)
```json
{
  "payment_hash": "abc123...",
  "paid": true,
  "status": "paid",
  "amount": 1000,
  "preimage": "def456..."
}
```

### Decode Invoice

```http
POST /api/invoice/decode
Content-Type: application/json
```

**Request Body**
```json
{
  "bolt11": "lnbc10n1pj..."
}
```

**Response** (200 OK)
```json
{
  "payment_hash": "abc123...",
  "amount_sat": 1000,
  "description": "Test payment",
  "expiry": 3600
}
```

### Get Wallet Balance

Requires authentication.

```http
GET /api/wallet/balance
Authorization: Bearer <token>
```

**Response** (200 OK)
```json
{
  "balance_sats": 100000,
  "balance_btc": 0.001,
  "wallet_id": "abc123..."
}
```

### Get Recent Payments

```http
GET /api/wallet/payments?limit=20
Authorization: Bearer <token>
```

## Webhooks

### LNbits Webhook

LNbits sends payment notifications to this endpoint when configured.

```http
POST /api/webhooks/lnbits
Content-Type: application/json
```

**Request Body** (from LNbits)
```json
{
  "payment_hash": "abc123...",
  "payment_request": "lnbc...",
  "amount": 10000,
  "memo": "CrowdPay: Campaign Title",
  "paid": true
}
```

**Response** (200 OK)
```json
{
  "message": "Payment processed"
}
```

### Setting Up Webhooks

1. Deploy your backend to a public URL
2. Set `LNBITS_WEBHOOK_URL` in your `.env`:
   ```
   LNBITS_WEBHOOK_URL=https://your-backend.com/api/webhooks/lnbits
   ```
3. The webhook URL is automatically added when creating invoices

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message description",
  "details": {} // Optional
}
```

### HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data or validation error
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Common Errors

**Validation Error**
```json
{
  "error": "Validation error",
  "details": [
    {
      "loc": ["amount"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error"
    }
  ]
}
```

**Payment Error**
```json
{
  "error": "Payment processing error",
  "details": "Insufficient balance in LNbits wallet"
}
```

## Payment Flow

```
Frontend                    Backend                     LNbits
   |                           |                           |
   |  POST /contributions      |                           |
   |-------------------------->|                           |
   |                           |  POST /api/v1/payments    |
   |                           |-------------------------->|
   |                           |  {payment_request, hash}  |
   |                           |<--------------------------|
   |  {payment_request, hash}  |                           |
   |<--------------------------|                           |
   |                           |                           |
   |  [Display QR Code]        |                           |
   |                           |                           |
   |  [User pays with wallet]  |                           |
   |                           |                           |
   |  GET /status (polling)    |                           |
   |-------------------------->|  GET /payments/{hash}     |
   |                           |-------------------------->|
   |                           |  {paid: true}             |
   |                           |<--------------------------|
   |  {is_paid: true}          |                           |
   |<--------------------------|                           |
   |                           |                           |
   |  [Show success]           |  [Update DB, campaign]    |
```

## Supported Currencies

**Lightning Network only:**
- `SATS` - Satoshis (recommended)
- `BTC` - Bitcoin (converted to SATS internally)

## Rate Limiting

Currently not implemented. Will be added in future versions.

## Support

For API issues:
- Check the main README.md
- Review test files for usage examples
- Open an issue on the repository
