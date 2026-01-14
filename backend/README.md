# CrowdPay MVP Backend

A Flask-based backend service for crowdfunding campaigns with Bitnob API integration for Bitcoin Lightning Network and fiat payments.

## Features

- **Campaign Management**: Create, update, and track fundraising campaigns
- **Contribution Tracking**: Accept and monitor contributions with real-time status updates
- **Lightning Payments**: Integration with Blink API for Bitcoin Lightning Network payments
- **Invoice Polling**: Automatic polling service to track payment confirmations
- **Database**: Supabase PostgreSQL backend with Row Level Security
- **RESTful API**: Well-structured API endpoints with proper error handling

## Technology Stack

- **Framework**: Flask 3.0
- **Database**: Supabase (PostgreSQL)
- **Payment Gateway**: Bitnob API (Lightning Network + Fiat)
- **Validation**: Pydantic models
- **Testing**: Pytest
- **Production Server**: Gunicorn

## Project Structure

```
backend/
├── app.py                      # Application entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── models/
│   ├── __init__.py
│   ├── campaign.py            # Campaign data model
│   └── contribution.py        # Contribution data model
├── routes/
│   ├── __init__.py
│   ├── campaigns.py           # Campaign endpoints
│   └── contributions.py       # Contribution endpoints
├── services/
│   ├── __init__.py
│   ├── bitnob.py              # Bitnob API integration
│   ├── invoice_polling.py    # Payment polling service
│   └── supabase_client.py    # Database client
├── tests/
│   ├── test_bitnob.py
│   ├── test_contributions.py
│   └── test_supabase.py
├── supabase_setup.sql         # Database schema
└── supabase_rls.sql           # Row Level Security policies
```

## Setup

### Prerequisites

- Python 3.9+
- Supabase account
- Bitnob API credentials

### Installation

1. **Clone and navigate to the backend directory**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the backend directory:
   ```env
   # Flask Configuration
   SECRET_KEY=your-secret-key-here
   FLASK_DEBUG=False

   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key

   # Bitnob API Configuration
   BITNOB_API_KEY=your-bitnob-api-key
   BITNOB_API_URL=https://api.bitnob.co
   BITNOB_WEBHOOK_SECRET=your-webhook-secret

   # Polling Configuration
   POLLING_INTERVAL=30
   POLLING_TIMEOUT=3600

   # CORS
   CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
   ```

5. **Set up database**
   
   Run the SQL scripts in your Supabase SQL editor:
   ```bash
   # First run supabase_setup.sql
   # Then run supabase_rls.sql
   ```

## Running the Application

### Development Mode

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Production Mode

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

For better production configuration:
```bash
gunicorn -w 4 \
  --bind 0.0.0.0:5000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  "app:create_app()"
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_blink.py -v
```

## API Endpoints

### Health Check
- `GET /health` - Check API health status

### Campaigns
- `POST /api/campaigns` - Create a new campaign
- `GET /api/campaigns` - List all campaigns (with filters)
- `GET /api/campaigns/<id>` - Get campaign details
- `PUT /api/campaigns/<id>` - Update campaign
- `DELETE /api/campaigns/<id>` - Cancel campaign
- `GET /api/campaigns/<id>/contributions` - Get campaign contributions

### Contributions
- `POST /api/contributions` - Create a new contribution
- `GET /api/contributions` - List contributions (with filters)
- `GET /api/contributions/<id>` - Get contribution details
- `GET /api/contributions/<id>/status` - Check payment status
- `POST /api/contributions/<id>/cancel` - Cancel pending contribution
- `POST /api/contributions/webhook` - Bitnob webhook endpoint

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Flask secret key | - | Yes |
| `FLASK_DEBUG` | Enable debug mode | False | No |
| `SUPABASE_URL` | Supabase project URL | - | Yes |
| `SUPABASE_KEY` | Supabase anon key | - | Yes |
| `BITNOB_API_KEY` | Bitnob API key | - | Yes |
| `BITNOB_API_URL` | Bitnob API endpoint | https://api.bitnob.co | No |
| `BITNOB_WEBHOOK_SECRET` | Webhook signature secret | - | Recommended |
| `POLLING_INTERVAL` | Invoice polling interval (seconds) | 30 | No |
| `POLLING_TIMEOUT` | Invoice polling timeout (seconds) | 3600 | No |
| `CORS_ORIGINS` | Allowed CORS origins | * | No |

## Database Schema

### Campaigns Table
- `id` (UUID, Primary Key)
- `title` (VARCHAR)
- `description` (TEXT)
- `target_amount` (DECIMAL)
- `current_amount` (DECIMAL)
- `currency` (VARCHAR)
- `creator_id` (VARCHAR)
- `creator_email` (VARCHAR)
- `status` (VARCHAR)
- `end_date` (TIMESTAMP)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Contributions Table
- `id` (UUID, Primary Key)
- `campaign_id` (UUID, Foreign Key)
- `contributor_name` (VARCHAR)
- `contributor_email` (VARCHAR)
- `amount` (DECIMAL)
- `currency` (VARCHAR)
- `payment_status` (VARCHAR)
- `bitnob_payment_id` (VARCHAR)
- `bitnob_payment_request` (TEXT)
- `bitnob_payment_hash` (VARCHAR)
- `bitnob_reference` (VARCHAR)
- `transaction_id` (VARCHAR)
- `message` (TEXT)
- `is_anonymous` (BOOLEAN)
- `created_at` (TIMESTAMP)
- `paid_at` (TIMESTAMP)

## Security

- Row Level Security (RLS) enabled on all tables
- API key authentication for Bitnob integration
- Webhook signature verification for security
- CORS configuration for frontend integration
- Input validation using Pydantic models
- Secure password handling (use environment variables)

## Error Handling

The API returns consistent error responses:

```json
{
  "error": "Error message description",
  "details": {} // Optional additional details
}
```

HTTP Status Codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `500` - Internal Server Error

## Payment Flow

1. User creates a contribution
2. Backend generates Bitnob payment (Lightning invoice or checkout)
3. User receives payment request (Lightning invoice or checkout URL)
4. Polling service monitors payment status
5. On payment confirmation:
   - Contribution status updated to "paid"
   - Campaign current_amount incremented
   - Polling stops

**Payment Methods Supported:**
- **Bitcoin/Lightning**: For BTC and SATS currencies
- **Fiat Currencies**: NGN, USD, and others via hosted checkout

## Development

### Adding New Endpoints

1. Define route in appropriate blueprint (`routes/campaigns.py` or `routes/contributions.py`)
2. Add validation using Pydantic models
3. Implement business logic
4. Add proper error handling
5. Write tests

### Database Migrations

When modifying the schema:
1. Update `supabase_setup.sql`
2. Update model classes in `models/`
3. Test locally
4. Apply changes to Supabase

## Troubleshooting

### Common Issues

**Issue**: `Configuration error: Missing required configuration`
- **Solution**: Ensure all required environment variables are set in `.env`

**Issue**: `Failed to create payment`
- **Solution**: Verify Bitnob API credentials and check API status

**Issue**: `Invalid webhook signature`
- **Solution**: Ensure BITNOB_WEBHOOK_SECRET matches your Bitnob dashboard settings

**Issue**: `Supabase connection failed`
- **Solution**: Check Supabase URL and key, ensure project is active

**Issue**: Polling not working
- **Solution**: Check POLLING_INTERVAL and ensure background threads are enabled

## Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Ensure tests pass
5. Submit a pull request

## License

MIT License

## Support

For issues and questions:
- Check API documentation in `API.md`
- Review test files for usage examples
- Open an issue on the repository