# CrowdPay API Documentation

Base URL: `http://localhost:5000` (development) or your production domain

## Table of Contents
- [Authentication](#authentication)
- [Health Check](#health-check)
- [Campaigns](#campaigns)
- [Contributions](#contributions)
- [Webhooks](#webhooks)
- [Error Responses](#error-responses)

## Authentication

The API uses Bitnob API key authentication for payment operations. Webhook endpoints verify signatures for security.

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
  "version": "1.0.0"
}
```

## Campaigns

### Create Campaign

Create a new fundraising campaign.

```http
POST /api/campaigns
Content-Type: application/json
```

**Request Body**
```json
{
  "title": "Community Event Fundraiser",
  "description": "Help us organize an amazing community event",
  "target_amount": 5000.00,
  "currency": "USD",
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
    "target_amount": 5000.00,
    "current_amount": 0.00,
    "currency": "USD",
    "creator_id": "user_123",
    "creator_email": "creator@example.com",
    "status": "active",
    "end_date": "2025-12-31T23:59:59Z",
    "created_at": "2025-01-07T10:30:00Z",
    "updated_at": "2025-01-07T10:30:00Z"
  }
}
```

### List Campaigns

Get all campaigns with optional filtering.

```http
GET /api/campaigns?status=active&creator_id=user_123&limit=10&offset=0
```

**Query Parameters**
- `status` (optional) - Filter by status: `active`, `completed`, `cancelled`, `expired`
- `creator_id` (optional) - Filter by creator
- `limit` (optional) - Number of results per page (default: 50)
- `offset` (optional) - Pagination offset (default: 0)

**Response** (200 OK)
```json
{
  "campaigns": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Community Event Fundraiser",
      "target_amount": 5000.00,
      "current_amount": 2500.00,
      "status": "active",
      "created_at": "2025-01-07T10:30:00Z"
    }
  ],
  "count": 1,
  "offset": 0,
  "limit": 10
}
```

### Get Campaign Details

Get detailed information about a specific campaign.

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
    "target_amount": 5000.00,
    "current_amount": 2500.00,
    "currency": "USD",
    "creator_id": "user_123",
    "status": "active",
    "created_at": "2025-01-07T10:30:00Z"
  },
  "statistics": {
    "progress_percentage": 50.0,
    "remaining_amount": 2500.00,
    "total_contributions": 25,
    "paid_contributions": 20,
    "is_goal_reached": false
  }
}
```

### Update Campaign

Update campaign details. Only the creator can update their campaign.

```http
PUT /api/campaigns/{campaign_id}
Content-Type: application/json
```

**Request Body**
```json
{
  "title": "Updated Campaign Title",
  "description": "Updated description",
  "target_amount": 6000.00,
  "status": "active"
}
```

**Allowed Fields**
- `title`
- `description`
- `target_amount`
- `status`
- `end_date`

**Response** (200 OK)
```json
{
  "message": "Campaign updated successfully",
  "campaign": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Updated Campaign Title",
    "target_amount": 6000.00,
    "updated_at": "2025-01-07T11:00:00Z"
  }
}
```

### Delete Campaign

Cancel a campaign (soft delete).

```http
DELETE /api/campaigns/{campaign_id}
```

**Response** (200 OK)
```json
{
  "message": "Campaign cancelled successfully"
}
```

### Get Campaign Contributions

List all contributions for a specific campaign.

```http
GET /api/campaigns/{campaign_id}/contributions
```

**Response** (200 OK)
```json
{
  "contributions": [
    {
      "id": "contrib_123",
      "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
      "contributor_name": "John Doe",
      "amount": 100.00,
      "payment_status": "paid",
      "message": "Great cause!",
      "created_at": "2025-01-07T10:45:00Z"
    },
    {
      "id": "contrib_124",
      "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
      "contributor_name": "Anonymous",
      "amount": 50.00,
      "payment_status": "paid",
      "is_anonymous": true,
      "created_at": "2025-01-07T11:00:00Z"
    }
  ],
  "count": 2
}
```

## Contributions

### Create Contribution

Create a new contribution and generate a payment. For Bitcoin/Lightning (BTC, SATS), generates a Lightning invoice. For fiat currencies (NGN, USD), generates a checkout URL.

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
  "amount": 100.00,
  "currency": "USD",
  "message": "Happy to support this cause!",
  "is_anonymous": false
}
```

**Response** (201 Created)

For Bitcoin/Lightning payments:
```json
{
  "message": "Contribution created successfully",
  "contribution": {
    "id": "contrib_123",
    "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
    "contributor_name": "John Doe",
    "amount": 100.00,
    "currency": "SATS",
    "payment_status": "pending",
    "bitnob_payment_id": "pay_abc123",
    "bitnob_reference": "contrib_xyz789",
    "message": "Happy to support this cause!",
    "created_at": "2025-01-07T10:45:00Z"
  },
  "payment_request": "lnbc1000n1p3..."
}
```

For fiat currency payments:
```json
{
  "message": "Contribution created successfully",
  "contribution": {
    "id": "contrib_123",
    "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
    "contributor_name": "John Doe",
    "amount": 5000.00,
    "currency": "NGN",
    "payment_status": "pending",
    "bitnob_payment_id": "checkout_abc123",
    "bitnob_reference": "contrib_xyz789",
    "created_at": "2025-01-07T10:45:00Z"
  },
  "payment_request": "https://checkout.bitnob.co/pay/abc123"
}
```

### Get Contribution Details

Get information about a specific contribution.

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
    "amount": 100.00,
    "currency": "USD",
    "payment_status": "paid",
    "paid_at": "2025-01-07T10:50:00Z",
    "transaction_id": "tx_hash_abc",
    "message": "Happy to support this cause!",
    "created_at": "2025-01-07T10:45:00Z"
  }
}
```

### Check Payment Status

Check the current payment status of a contribution.

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

### Cancel Contribution

Cancel a pending contribution.

```http
POST /api/contributions/{contribution_id}/cancel
```

**Response** (200 OK)
```json
{
  "message": "Contribution cancelled successfully"
}
```

### List Contributions

Get all contributions with optional filtering.

```http
GET /api/contributions?campaign_id=550e8400...&payment_status=paid&limit=20&offset=0
```

**Query Parameters**
- `campaign_id` (optional) - Filter by campaign
- `payment_status` (optional) - Filter by status: `pending`, `paid`, `failed`, `expired`, `cancelled`
- `limit` (optional) - Number of results per page (default: 50)
- `offset` (optional) - Pagination offset (default: 0)

**Response** (200 OK)
```json
{
  "contributions": [
    {
      "id": "contrib_123",
      "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
      "contributor_name": "John Doe",
      "amount": 100.00,
      "payment_status": "paid",
      "created_at": "2025-01-07T10:45:00Z"
    }
  ],
  "count": 1,
  "offset": 0,
  "limit": 20
}
```

### Bitnob Webhook

Webhook endpoint for Bitnob payment notifications. Signature verification required.

```http
POST /api/contributions/webhook
Content-Type: application/json
X-Bitnob-Signature: <signature>
```

**Request Body** (from Bitnob)
```json
{
  "event": "charge:success",
  "data": {
    "reference": "contrib_xyz789",
    "status": "success",
    "paidAt": "2025-01-07T10:50:00Z",
    "transactionId": "tx_hash_abc",
    "amount": 100.00,
    "currency": "NGN"
  }
}
```

**Event Types:**
- `charge:success` - Payment successful
- `charge:failed` - Payment failed
- `charge:pending` - Payment pending

**Response** (200 OK)
```json
{
  "message": "Webhook processed successfully"
}
```

## Webhooks

### Setting Up Webhooks

1. Log into your Bitnob dashboard
2. Navigate to Settings > Webhooks
3. Add your webhook URL: `https://yourdomain.com/api/contributions/webhook`
4. Copy the webhook secret
5. Add the secret to your `.env` file as `BITNOB_WEBHOOK_SECRET`

### Webhook Security

All webhooks are verified using HMAC-SHA256 signatures. The signature is included in the `X-Bitnob-Signature` header and must match the expected signature for the payload.

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message description"
}
```

For validation errors:
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

### HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data or validation error
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Payment Statuses

### Contribution Payment Status
- `pending` - Awaiting payment
- `paid` - Payment confirmed
- `failed` - Payment failed
- `expired` - Payment invoice expired
- `cancelled` - Contribution cancelled

### Campaign Status
- `active` - Campaign is active and accepting contributions
- `completed` - Campaign goal reached or ended successfully
- `cancelled` - Campaign cancelled by creator
- `expired` - Campaign end date passed

## Rate Limiting

Currently, no rate limiting is implemented. This will be added in future versions.

## Supported Currencies

- **Bitcoin/Lightning**: BTC, SATS
- **Fiat**: NGN (Nigerian Naira), USD (US Dollar), and others supported by Bitnob

## Payment Methods

- **Lightning Network**: Instant Bitcoin payments for BTC/SATS
- **Hosted Checkout**: Card payments and other methods for fiat currencies

## Webhooks

Configure the Bitnob webhook URL in your Bitnob dashboard:
```
https://yourdomain.com/api/contributions/webhook
```

Ensure webhook signature verification is enabled by setting `BITNOB_WEBHOOK_SECRET` in your environment.

## Support

For API issues or questions, please refer to the main README.md or open an issue on the repository.