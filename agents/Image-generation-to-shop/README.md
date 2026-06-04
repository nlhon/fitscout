# Image-generation-to-shop Agent

An intelligent AI agent that generates outfit images and automatically finds shopping links to purchase matching items.

## Overview

The Image-generation-to-shop Agent combines two powerful APIs:
1. **Replicate** - Generates high-quality outfit images using flux-schnell model
2. **SerpApi Google Lens** - Finds retail products matching the generated outfits

This creates a seamless workflow: User describes an outfit → AI generates visual → Finds shopping links.

## Key Features

- **AI-Powered Image Generation**: Create professional outfit photos from text descriptions
- **Automated Shopping Discovery**: Find where to buy matching items using Google Lens
- **Multi-Variation Support**: Generate multiple outfit variations and find shopping links for each
- **FastAPI Integration**: RESTful API with automatic OpenAPI documentation
- **Category Filtering**: Filter shopping results by product category
- **Error Handling**: Graceful degradation with detailed error messages
- **Production Ready**: Docker containerization and health checks included

## Architecture

```
User Prompt
    ↓
[Image Generation Service]
    ↓ (Replicate API)
Outfit Image URL
    ↓
[Shopping Search Service]
    ↓ (SerpApi Google Lens)
Shopping Results
    ↓
User Response
```

## API Endpoints

### Main Endpoints

**POST /api/v1/outfit-to-shop**
- Generate single outfit + find shopping matches
- Request: User prompt describing outfit
- Response: Generated image + shopping results

**POST /api/v1/multi-outfit-to-shop**
- Generate multiple outfit variations + find shopping for each
- Request: User prompt + count (1-10)
- Response: Multiple images + aggregated shopping results

**POST /api/v1/search-shopping**
- Search for shopping matches for an existing image URL
- Request: Image URL + optional category filter
- Response: Shopping results for the image

### Status Endpoints

**GET /health** - Health check with API configuration status  
**GET /** - Service information

## Quick Start

### Prerequisites
- Python 3.12+
- Replicate API key (free tier available at https://replicate.com)
- SerpApi API key (free tier available at https://serpapi.com)

### Installation

```bash
# Clone repository
git clone https://github.com/wongyongsheng/fitscout.git
cd agents/Image-generation-to-shop

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp config/.env.example config/.env
# Edit config/.env with your API keys
```

### Running the Server

**Development Mode:**
```bash
python src/main.py
# Server running on http://localhost:8001
# API docs at http://localhost:8001/docs
```

**Production Mode (Docker):**
```bash
docker build -t image-generation-to-shop:latest .
docker run -p 8001:8001 --env-file config/.env image-generation-to-shop:latest
```

## Usage Examples

### Single Outfit Generation

```bash
curl -X POST http://localhost:8001/api/v1/outfit-to-shop \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "casual summer dress with sandals",
    "style": "casual"
  }'
```

**Response:**
```json
{
  "request_id": "abc-123",
  "status": "success",
  "outfit_image_url": "https://...",
  "shopping_results": [
    {
      "title": "Summer Dress",
      "source": "ASOS",
      "link": "https://asos.com/...",
      "price": "$45",
      "thumbnail": "https://...",
      "rating": "4.5",
      "reviews": "128"
    }
  ],
  "total_results": 5,
  "processing_time_ms": 2500,
  "message": "Successfully generated outfit and found 5 shopping matches"
}
```

### Multiple Outfit Variations

```bash
curl -X POST http://localhost:8001/api/v1/multi-outfit-to-shop \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "professional business blazer outfit",
    "count": 3
  }'
```

### Search Shopping for Existing Image

```bash
curl -X POST http://localhost:8001/api/v1/search-shopping \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/outfit.jpg",
    "category": "shoes"
  }'
```

## Project Structure

```
agents/Image-generation-to-shop/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Production container
├── config/
│   ├── settings.py             # Configuration management
│   └── .env.example            # Environment template
├── src/
│   ├── main.py                 # FastAPI app initialization
│   ├── api/
│   │   ├── endpoints.py        # API routes (3 main endpoints)
│   │   └── models.py           # Pydantic request/response schemas
│   └── services/
│       ├── image_generator.py  # Replicate image generation
│       └── shopping_searcher.py # SerpApi shopping search
└── tests/
    ├── test_endpoints.py       # API endpoint tests
    ├── test_services.py        # Service unit tests
    └── conftest.py             # Test configuration
```

## Configuration

Environment variables in `config/.env`:

```bash
# REQUIRED - API Keys
REPLICATE_API_TOKEN=your_token_here
SERPAPI_API_KEY=your_key_here

# OPTIONAL - Server
HOST=0.0.0.0
PORT=8001
DEBUG=False

# OPTIONAL - Image Generation
IMAGE_MODEL=black-forest-labs/flux-schnell
GUIDANCE_SCALE=3.5
INFERENCE_STEPS=4

# OPTIONAL - Search
SEARCH_ENGINE=google_lens
SEARCH_TIMEOUT=30

# OPTIONAL - Logging
LOG_LEVEL=INFO
```

## API Keys

### Replicate
1. Visit https://replicate.com/
2. Sign up (free tier: 1000 free API calls per month)
3. Go to API tokens page
4. Copy token to `REPLICATE_API_TOKEN`

### SerpApi
1. Visit https://serpapi.com/
2. Sign up (free tier: 100 searches per month)
3. Go to API dashboard
4. Copy API key to `SERPAPI_API_KEY`

## Performance

| Operation | Time | Cost |
|-----------|------|------|
| Image Generation | 2-5s | ~$0.01 per image |
| Shopping Search | 1-2s | ~$0.01 per search |
| Total (1 outfit) | 3-7s | ~$0.02 |
| Total (10 outfits) | 30-70s | ~$0.20 |

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_endpoints.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Deployment

### Docker Deployment
```bash
docker build -t image-generation-to-shop:latest .
docker run -p 8001:8001 --env-file config/.env image-generation-to-shop:latest
```

### Cloud Run (GCP)
```bash
gcloud run deploy image-generation-to-shop \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars REPLICATE_API_TOKEN=xxx,SERPAPI_API_KEY=yyy
```

### Kubernetes
```bash
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

## Error Handling

The agent handles common errors gracefully:

- **Missing API Keys**: Returns 500 with clear error message
- **Image Generation Failure**: Returns 500 with detailed error
- **Shopping Search Timeout**: Returns 500 with timeout message
- **Invalid Prompts**: Returns 400 for validation errors
- **Network Issues**: Timeout handling with retry logic

## Future Enhancements

- [ ] Add caching layer (Redis) for repeated searches
- [ ] Support for different image models (DALL-E, Midjourney)
- [ ] Multi-language prompt support
- [ ] Price comparison across retailers
- [ ] Size recommendation based on image
- [ ] Social media integration (Pinterest, TikTok)
- [ ] User preference learning and personalization

## License

MIT

## Support

- **API Docs**: http://localhost:8001/docs (interactive Swagger UI)
- **GitHub**: https://github.com/wongyongsheng/fitscout
- **Issues**: Report bugs on GitHub Issues

---

**Status**: Production Ready  
**Created for**: Microsoft Hackathon 2026
