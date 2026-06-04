# Fashion Discovery Sub-Agent

A sophisticated agent that discovers luxury fashion retailers through Agent-to-Agent (A2A) protocol integration. Combines intelligent web search with a curated retailer registry to find high-end fashion brands matching user queries.

## Overview

The Fashion Discovery Sub-Agent is designed for larger fashion assistant ecosystems, implementing:

- **Multi-Stage Discovery**: Registry lookup → Tavily web search → Optional real-time agent calls
- **A2A Protocol Integration**: Standard HTTP endpoints for agent-to-agent communication
- **Micropayment Support**: X402 protocol ready for XRPL-based transactions
- **Luxury Brand Focus**: Curated blacklist of mass-market retailers (Amazon, Shein, etc.)
- **NLP Query Processing**: Regex-based intent classification without external ML dependencies

## Architecture

```
Orchestrator Agent
       │ POST /api/v1/fashion-discovery
       ▼
┌─────────────────────────────────┐
│ Fashion Discovery Sub-Agent     │
├─────────────────────────────────┤
│ 1. Query Parser (NLP)           │
│    ↓                            │
│ 2. Registry Lookup              │
│    ├─→ Matches Found? Return    │
│    └─→ No? Continue              │
│    ↓                            │
│ 3. Tavily Web Search (fallback) │
│    ├─→ Blacklist-aware          │
│    └─→ Sync to registry         │
│    ↓                            │
│ 4. Agent Connector (A2A Proto)  │
│    ├─→ Parallel calls           │
│    └─→ Handle X402 Payments     │
│    ↓                            │
│ 5. Response Assembly            │
└─────────────────────────────────┘
       │
       ├→ Retailer 1 Agent
       ├→ Retailer 2 Agent
       └→ Retailer N Agent
```

## Key Features

- **Multi-Stage Discovery Pipeline**: Registry → Web Search → Agent Calls (with fallbacks)
- **Curated Registry**: Maintains whitelist of 50+ luxury retailers (verified by quality tier)
- **Tavily Search Integration**: AI-ready web search with automatic blacklist exclusion
- **A2A Protocol**: HTTP-based agent discovery and communication
- **X402 Micropayments**: Payment negotiation for premium retailer access
- **NLP Query Parser**: Extracts price, category, quality tier, intent without ML
- **Comprehensive Testing**: 35+ tests covering all components
- **Production Ready**: Docker containerization, error handling, database persistence

## Project Structure

```
agents/fashion-discovery/
├── README.md                    # This file
├── QUICKSTART.md               # Setup and usage guide
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Production container
├── manage.py                   # CLI tools (init-db, seed-db, stats)
│
├── config/
│   ├── settings.py            # Pydantic configuration management
│   └── .env.example           # Template for environment variables
│
├── src/
│   ├── main.py               # FastAPI app initialization
│   ├── database/             # ORM and persistence
│   │   ├── __init__.py
│   │   ├── models.py         # SQLAlchemy: Retailer, BlacklistEntry, SearchQuery
│   │   └── seed.py           # Database utilities
│   ├── api/
│   │   ├── endpoints.py      # FastAPI routes (discovery, health, stats)
│   │   └── models.py         # Pydantic request/response schemas
│   ├── services/
│   │   ├── registry.py       # Retailer CRUD and blacklist validation
│   │   ├── tavily_search.py  # Tavily API integration
│   │   ├── query_processor.py # NLP query parsing
│   │   └── agent_connector.py # A2A protocol calls
│   └── fixtures/
│       └── sample_data.py    # 8 sample retailers + blacklist
│
├── tests/
│   ├── test_query_processor.py  # 11 NLP tests
│   ├── test_registry.py         # 14 registry tests
│   └── test_api.py              # 10 API endpoint tests
│
└── kubernetes/
    ├── deployment.yaml
    ├── service.yaml
    └── configmap.yaml
```

## Core Components

### 1. Query Parser (services/query_processor.py)
Converts natural language queries into structured search parameters:

```python
# Input: "luxury puffer jackets under $5000"
# Output:
{
  "product_type": ["outerwear"],
  "style": ["classic"],
  "price_range": {"max": 5000},
  "quality_tier": "luxury",
  "intent": "product_search"
}
```

### 2. Registry Service (services/registry.py)
SQLAlchemy-based ORM for retailer management:

**Sample Retailers:**
- House of Nova, Dover Street Market, SSENSE, Browns Fashion
- Farfetch, Vestiaire Collective, TheRealReal, MATCHES FASHION

**Blacklist (16+ entries):**
Amazon, Temu, Shein, Fashion Nova, H&M, Zara, Target, Walmart, eBay, AliExpress, Etsy, Forever21, Boohoo, ASOS, PrettyLittleThing

### 3. Tavily Search (services/tavily_search.py)
Intelligent web search with:
- Automatic blacklist enforcement
- Confidence scoring (domain + content analysis)
- Category extraction from results
- Error handling and graceful degradation

### 4. Agent Connector (services/agent_connector.py)
A2A Protocol implementation:
- Parallel HTTP calls to retailer agent endpoints
- X402 Payment Required response handling
- Result aggregation and relevance scoring

### 5. FastAPI Endpoints (api/endpoints.py)
RESTful discovery interface with 6 endpoints.

## Data Models

### Retailer
```python
retailer_id: UUID (unique)
name: str
website_url: str
agent_endpoint: str
quality_tier: enum (luxury, premium, emerging)
categories: json (clothing types)
x402_payment_address: str (XRPL wallet)
verification_score: float (0-1)
last_verified: datetime
```

### BlacklistEntry
```python
domain: str (unique)
reason: str
is_active: bool
```

### SearchQuery
```python
request_id: UUID
agent_id: str
query: str
filters: json
results_count: int
query_cost: float
response_time_ms: int
```

## Multi-Stage Discovery Flow

1. **Registry Lookup** - Query local database with filters
2. **Fallback (If <3 results)** - Tavily web search with automatic blacklist
3. **Agent Calls (Optional)** - Call retailer agents in parallel if X402 budget available
4. **Response Assembly** - Aggregate results, calculate costs, log query

## Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | FastAPI 0.104+ | Web framework & async support |
| Database | SQLAlchemy 2.0+ | ORM & PostgreSQL/SQLite |
| Search | Tavily 0.2.1 | Intelligent web search |
| HTTP Client | httpx 0.25+ | Async A2A protocol calls |
| Payments | XRPL 2.10.0 | X402 micropayment support |
| Testing | pytest 7.4+ | Comprehensive test coverage |
| Containerization | Docker | Production deployment |

## Quick Start

```bash
# 1. Setup
git clone https://github.com/wongyongsheng/fitscout.git
cd agents/fashion-discovery

# 2. Environment
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp config/.env.example config/.env
# Edit with TAVILY_API_KEY

# 4. Initialize
python manage.py init-db
python manage.py seed-db

# 5. Run
python src/main.py

# 6. Test
pytest tests/ -v
```

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

## API Examples

### Basic Discovery

```bash
curl -X POST http://localhost:8000/api/v1/fashion-discovery \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "orchestrator-1",
    "request_id": "query-123",
    "query": "luxury designer shoes"
  }'
```

### Response

```json
{
  "request_id": "query-123",
  "matches": [
    {
      "retailer_id": "farfetch-001",
      "retailer_name": "Farfetch",
      "website_url": "https://farfetch.com",
      "agent_endpoint": "https://farfetch.com/api/fashion-agent",
      "category": "luxury-designer-shoes",
      "confidence_score": 0.98,
      "x402_endpoint": "https://farfetch.com/x402"
    }
  ],
  "total_matches": 5,
  "query_cost": 0.001,
  "message": "Found 5 luxury fashion retailers"
}
```

## Testing

35+ comprehensive tests:

```bash
pytest tests/ -v                    # Run all tests
pytest tests/test_query_processor.py -v  # NLP tests
pytest tests/test_registry.py -v         # Registry tests
pytest tests/test_api.py -v              # API tests
pytest tests/ --cov=src --cov-report=html # With coverage
```

## Configuration

Environment variables in `config/.env`:

```bash
TAVILY_API_KEY=tvly-xxxxx              # Required
DATABASE_URL=postgresql://user:pass... # Optional
XRPL_WALLET_ADDRESS=rXxxx...          # Optional
XRPL_NETWORK=testnet                   # Optional
LOG_LEVEL=INFO                         # Optional
CACHE_TTL=3600                         # Optional
```

## Deployment

### Docker
```bash
docker build -t fashion-discovery:latest .
docker run -p 8000:8000 --env-file config/.env fashion-discovery:latest
```

### Cloud Run (GCP)
```bash
gcloud run deploy fashion-discovery --source . \
  --set-env-vars TAVILY_API_KEY=tvly-xxxxx
```

### Kubernetes
```bash
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

## Performance

| Metric | Value |
|--------|-------|
| Registry Lookup | <100ms |
| Tavily Search | 500-1500ms |
| Agent Calls | 2-5s (parallel) |
| Total Response | 500ms - 6s |
| Query Cost | $0 - $0.01 |

## License

MIT

## Support

- **Setup**: [QUICKSTART.md](QUICKSTART.md)
- **API Docs**: http://localhost:8000/docs
- **Plan**: [../FASHION_DISCOVERY_AGENT_PLAN.md](../FASHION_DISCOVERY_AGENT_PLAN.md)

---

**Status**: Production Ready (Phase 4 Complete)  
**Created for**: Microsoft Hackathon 2026
```

## Technology Stack

- **Runtime**: Python 3.12+
- **Framework**: FastAPI
- **Registry**: PostgreSQL or MongoDB
- **Search**: Tavily API
- **A2A Protocol**: OpenAPI/OpenAgent spec
- **Payments**: XRPL client library
- **Caching**: Redis
- **Testing**: pytest

## Getting Started

### Prerequisites
- Python 3.12+
- Tavily API Key
- X402-capable wallet (for micropayments)
- Database (PostgreSQL/MongoDB)

### Installation

```bash
# Clone the repository
git clone https://github.com/wongyongsheng/fitscout.git
cd agents/fashion-discovery

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config/.env.example config/.env
# Edit config/.env with your credentials
```

### Running the Agent

```bash
python src/main.py
```

The agent will start on `http://localhost:8000` with A2A endpoint at `/api/v1/fashion-discovery`.

## Documentation

See [FASHION_DISCOVERY_AGENT_PLAN.md](../../FASHION_DISCOVERY_AGENT_PLAN.md) for detailed technical plan and architecture.

## Contributors

- [Your Name]
- Team members

## License

MIT

---

For more details on the technical plan, see the project root documentation.
