# Quick Start Guide - Fashion Discovery Sub-Agent

## Prerequisites

- Python 3.12+
- PostgreSQL 12+ or SQLite (development)
- Tavily API Key (for web search)
- XRPL Wallet Address (optional, for X402 payments)

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/wongyongsheng/fitscout.git
cd agents/fashion-discovery
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy example config
cp config/.env.example config/.env

# Edit with your credentials
nano config/.env
```

**Required Configuration:**
- `TAVILY_API_KEY`: Get from https://tavily.com
- `DATABASE_URL`: PostgreSQL connection string (optional, defaults to SQLite)

**Optional Configuration:**
- `X402_WALLET_ADDRESS`: Your XRPL wallet address
- `XRPL_NETWORK`: testnet or mainnet
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR

### 5. Initialize Database
```bash
# Create database and tables
python manage.py init-db

# Load sample data
python manage.py seed-db

# Check stats
python manage.py stats
```

## Running the Agent

### Development Mode
```bash
# Start with auto-reload
python src/main.py

# Or with uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
# Using Gunicorn (recommended)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app

# Using Docker
docker build -t fashion-discovery:latest .
docker run -p 8000:8000 --env-file config/.env fashion-discovery:latest
```

## Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
# Query processor tests
pytest tests/test_query_processor.py -v

# Registry tests
pytest tests/test_registry.py -v

# API endpoint tests
pytest tests/test_api.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Fashion Discovery (Main Endpoint)

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/fashion-discovery \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "orchestrator-1",
    "request_id": "query-123",
    "query": "luxury puffer jackets under $5000",
    "filters": {
      "max_price": 5000,
      "categories": ["outerwear"],
      "quality_tiers": ["luxury", "premium"]
    },
    "x402_budget": 0.05
  }'
```

**Response:**
```json
{
  "request_id": "query-123",
  "matches": [
    {
      "retailer_id": "house-of-nova-001",
      "retailer_name": "House of Nova",
      "website_url": "https://houseofnova.xyz",
      "agent_endpoint": "https://houseofnova.xyz/api/agent",
      "category": "luxury-puffer-jackets",
      "confidence_score": 0.95,
      "x402_endpoint": "https://houseofnova.xyz/payments"
    }
  ],
  "total_matches": 5,
  "query_cost": 0.001,
  "message": "Found 5 luxury fashion retailers matching your criteria"
}
```

### Registry Health
```bash
curl http://localhost:8000/api/v1/registry/health
```

### Statistics
```bash
curl http://localhost:8000/api/v1/statistics
```

## Database Management

### Initialize Clean Database
```bash
python manage.py reset-db
```

### Add New Retailer
```bash
# Use the FastAPI docs at http://localhost:8000/docs
# Or add programmatically via code
```

### Query Statistics
```bash
python manage.py stats
```

## Troubleshooting

### Tavily API Errors
- Check API key is correct: `echo $TAVILY_API_KEY`
- Verify API key has sufficient quota
- Check rate limiting: https://tavily.com/dashboard

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -U postgres -h localhost -d fitscout_db

# Or use SQLite (default)
sqlite3 fashion_discovery.db ".tables"
```

### Blacklist Configuration
The agent automatically excludes these domains:
- amazon.com, temu.com, shein.com, fashionnova.com
- h&m.com, zara.com, target.com, walmart.com
- ebay.com, aliexpress.com, etsy.com, and more

## Performance Tuning

### Caching
- Results cached for 1 hour by default
- Configure: `CACHE_TTL` in settings

### Database Optimization
- Add indexes on: `retailer_id`, `status`, `quality_tier`
- Regular VACUUM and ANALYZE for PostgreSQL

### Rate Limiting
- Configure per-agent limits in production
- Use Redis for distributed rate limiting

## Monitoring

### Log Files
```bash
# Check logs in console output
# Or configure file logging in settings.py
```

### Metrics
- Query count and response times via `/api/v1/statistics`
- Query logs stored in `search_queries` table
- Registry stats via `/api/v1/registry/health`

## Next Steps

1. **Customize Retailer Registry**: Edit `src/fixtures/sample_data.py`
2. **Add Authentication**: Implement JWT or API key auth
3. **Configure X402 Payments**: Set up XRPL wallet for micropayments
4. **Deploy to Production**: Use Docker + Kubernetes or Cloud Run
5. **Set Up Monitoring**: Use Datadog, NewRelic, or Prometheus

## Support

For issues or questions:
1. Check the [Technical Plan](../../FASHION_DISCOVERY_AGENT_PLAN.md)
2. Review API documentation: http://localhost:8000/docs
3. Check test cases for usage examples

## License

MIT
