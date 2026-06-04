# Fashion Discovery Sub-Agent

A specialized AI agent for discovering luxury fashion retailers with AI capabilities.

## Overview

This sub-agent serves as a critical hub between the central orchestrator and distributed luxury fashion retailers. It maintains a curated registry of high-end fashion retailers and uses Tavily API for intelligent web searches, handling discovery queries, registry lookups, and facilitating micropayments via X402 protocol.

## Key Features

- **Curated Registry**: Maintains a whitelist of luxury fashion retailers (no mass-market sites)
- **Tavily Search Integration**: AI-ready web search with automatic blacklist exclusion
- **A2A Protocol**: Discoverable via Agent-to-Agent protocol for orchestrator coordination
- **X402 Micropayments**: Support for payment negotiation with retailers
- **Real-time Verification**: Verify retailer availability and inventory

## Project Structure

```
agents/fashion-discovery/
├── README.md
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── registry.json
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints.py
│   │   └── models.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── registry.py
│   │   ├── tavily_search.py
│   │   ├── query_processor.py
│   │   ├── agent_connector.py
│   │   └── payment.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── validators.py
├── tests/
│   ├── __init__.py
│   ├── test_registry.py
│   ├── test_query_processor.py
│   └── test_api.py
└── Dockerfile
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
