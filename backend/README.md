# CrowdPay Backend

A robust Flask-based crowdfunding platform backend with Bitcoin and M-Pesa payment integration.

##  Features

- **Multi-Payment Support**: M-Pesa via Minmo API, Lightning Network Bitcoin payments
- **Real-time Updates**: Webhook handling for payment status updates
- **Database Integration**: PostgreSQL via Supabase with real-time capabilities
- **Secure API**: CORS-enabled, webhook signature verification, environment-based configuration
- **Production Ready**: Gunicorn WSGI server, comprehensive error handling, logging

##9 Project Structure

```
backend/
├── app.py                      # Flask application factory and main entry point
├── requirements.txt            # Python dependencies
├── .env                       # Environment variables (not in git)
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── API.md                    # API documentation
├── README.md                 # This file
├── 
├── routes/                   # API route handlers
│   ├── __init__.py          # Package initializer
│   ├── links.py            # Payment link/campaign endpoints
│   ├── contributions.py    # Donation/contribution endpoints
│   └── webhooks.py         # Payment provider webhook handlers
├── 
├── services/                # Business logic and integrations
│   ├── __init__.py         # Package initializer
│   ├── supabase_client.py  # Database client configuration
│   ├── minmo.py           # Minmo API integration (M-Pesa, Bank)
│   └── lightning.py       # Lightning Network integration
├── 
├── supabase_setup.sql      # Database schema and initial data
├── supabase_rls.sql        # Row Level Security policies
├── 
└── tests/                  # Test files
    ├── test_supabase.py    # Database connection tests
    ├── test_minmo.py      # Minmo integration tests
    └── test_db_quick.py   # Quick database functionality tests
```

## Tech Stack

- **Framework**: Flask 3.1.2 with Flask-CORS
- **Database**: PostgreSQL via Supabase
- **Payment Providers**: 
  - Minmo (M-Pesa, Bank Transfers)
  - Lightning Network (Bitcoin)
- **Authentication**: Supabase Auth integration
- **Deployment**: Gunicorn WSGI server
- **Environment**: Python 3.10+

## Prerequisites

- Python 3.10 or higher
- PostgreSQL database (or Supabase account)
- Minmo API credentials (for M-Pesa integration)
- Lightning Network provider credentials

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/DadaDevelopers/crowdpay-mvp-crowdpay.git
cd crowdpay-mvp-crowdpay/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\Scripts\\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
vi .env
```

Required environment variables:
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Payment Provider Configuration
MINMO_API_KEY=your-minmo-api-key
MINMO_BASE_URL=https://api.minmo.com
MINMO_WEBHOOK_SECRET=your-webhook-secret

# Lightning Network (optional)
LIGHTNING_API_KEY=your-lightning-provider-key
LIGHTNING_BASE_URL=https://api.your-lightning-provider.com

# Flask Configuration
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
FLASK_ENV=development

# Frontend URL (for CORS)
FRONTEND_URL=https://your-frontend-domain.com
```

### 3. Database Setup

1. **Create Supabase Project**:
   - Go to [supabase.com](https://supabase.com)
   - Create new project
   - Get your URL and Service Role Key

2. **Run Database Schema**:
   - Open Supabase Dashboard → SQL Editor
   - Copy and run contents of `supabase_setup.sql`
   - Run contents of `supabase_rls.sql` for security policies

3. **Test Database Connection**:
   ```bash
   python tests/test_supabase.py
   ```

### 4. Start Development Server

```bash
# Using Flask development server
python app.py

# Or using Flask CLI
flask run

# Server will start at http://localhost:5000
```

### 5. Test API

```bash
# Test root endpoint
curl http://localhost:5000/

# Create a test campaign
curl -X POST http://localhost:5000/api/links/create \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Test Campaign",
    "description": "A test crowdfunding campaign",
    "goal_kes": 50000,
    "visibility": "public"
  }'
```

## 🔗 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/api/links/create` | Create new campaign |
| `GET` | `/api/links/{slug}` | Get campaign details |
| `POST` | `/api/contributions/create` | Create contribution |
| `GET` | `/api/contributions/{id}` | Get contribution status |
| `POST` | `/api/webhooks/minmo` | Minmo payment webhooks |
| `POST` | `/api/webhooks/lightning` | Lightning payment webhooks |

### Example Usage

**Create Campaign**:
```bash
curl -X POST http://localhost:5000/api/links/create \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Help Sarah Buy a Laptop",
    "description": "Sarah needs a laptop for coding",
    "goal_kes": 75000,
    "visibility": "public"
  }'
```

**Create Contribution**:
```bash
curl -X POST http://localhost:5000/api/contributions/create \\
  -H "Content-Type: application/json" \\
  -d '{
    "link_id": "campaign-uuid",
    "amount_kes": 5000,
    "payment_method": "mpesa",
    "donor_name": "John Doe",
    "donor_email": "john@example.com"
  }'
```

## Database Schema

### Core Tables

- **`payment_links`**: Campaign/fundraising link data
- **`contributions`**: Individual donations and their status
- **`webhook_events`**: Payment provider webhook logs for debugging

### Key Features

- **Auto-updating totals**: Campaign totals update automatically when contributions are completed
- **Audit trail**: All webhook events are logged with timestamps
- **Row Level Security**: Configurable access policies
- **Real-time subscriptions**: Frontend can subscribe to changes

## Security Features

### API Security
- **CORS Configuration**: Restricts frontend origins
- **Webhook Signature Verification**: HMAC-SHA256 verification for all payment webhooks
- **Environment Variables**: Sensitive data never hardcoded
- **Input Validation**: All endpoints validate required fields

### Database Security
- **Service Role vs Anon Key**: Backend uses service role, frontend uses anon key
- **Row Level Security**: Database-level access control
- **SQL Injection Protection**: ORM-based queries via Supabase client

### Production Security Checklist
- [ ] Enable HTTPS/TLS
- [ ] Set secure webhook secrets
- [ ] Configure firewall rules
- [ ] Enable database SSL
- [ ] Set up monitoring and alerts
- [ ] Regular security updates

## Deployment

### Using Gunicorn (Recommended)

```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Start production server
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# With configuration file
gunicorn -c gunicorn.conf.py app:app
```

### Environment-Specific Configurations

**Development**:
```bash
export FLASK_ENV=development
python app.py
```

**Production**:
```bash
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Platform Deployment Examples

**Railway**:
1. Connect GitHub repository
2. Set environment variables in dashboard
3. Deploy automatically on push

**Render**:
1. Create new Web Service
2. Connect repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn app:app`

**DigitalOcean App Platform**:
```yaml
name: crowdpay-backend
services:
- name: api
  source_dir: /backend
  github:
    repo: DadaDevelopers/crowdpay-mvp-crowdpay
    branch: main
  run_command: gunicorn app:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: SUPABASE_URL
    value: your-url
  - key: SUPABASE_SERVICE_ROLE_KEY
    value: your-key
```

## Testing

### Run All Tests
```bash
# Test database connection
python tests/test_supabase.py

# Test Minmo integration
python tests/test_minmo.py

# Quick database functionality test
python tests/test_db_quick.py
```

### Manual API Testing
```bash
# Start server
python app.py

# Test endpoints
curl http://localhost:5000/
curl http://localhost:5000/api/links/help-john-startup
```

## Troubleshooting

### Common Issues

**Database Connection Errors**:
```bash
# Check environment variables
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'URL: {os.getenv(\"SUPABASE_URL\")}')"

# Test connection
python tests/test_supabase.py
```

**Import Errors**:
```bash
# Ensure virtual environment is activated
which python
pip list | grep flask

# Reinstall dependencies
pip install -r requirements.txt
```

**CORS Issues**:
- Check `FRONTEND_URL` environment variable
- Verify frontend origin in CORS configuration
- Check browser console for CORS errors

**Webhook Issues**:
- Verify webhook URLs are publicly accessible
- Check webhook secret configuration
- Review webhook logs in database

### Debug Mode

```bash
# Enable detailed logging
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

## Additional Documentation

- [API Documentation](API.md) - Detailed API reference
- [Database Schema](supabase_setup.sql) - Complete database structure
- [Security Policies](supabase_rls.sql) - Row level security setup

##  Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Workflow

```bash
# Setup development environment
python -m venv venv
source venv/bin/activate  # or venv\\Scripts\\activate on Windows
pip install -r requirements.txt

# Make changes and test
python app.py
python tests/test_supabase.py

# Before committing
pip freeze > requirements.txt
git add .
git commit -m "Your descriptive commit message"
```

## Support

- **Issues**: [GitHub Issues](https://github.com/DadaDevelopers/crowdpay-mvp-crowdpay/issues)
