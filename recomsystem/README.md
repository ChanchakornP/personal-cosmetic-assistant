# Recommendation System

AI-powered cosmetic product recommendation system for personal cosmetic assistant.

## Project Structure

```
recomsystem/
├── main.py                      # FastAPI application entry point
├── requirement.txt              # Python dependencies
├── .env.example                 # Environment variables template
├── IMPLEMENTATION_PLAN.md       # Detailed implementation plan
├── models/
│   ├── __init__.py
│   └── dtos.py                  # Data Transfer Objects (DTOs)
├── services/
│   ├── __init__.py
│   └── product_client.py        # Product API client service
├── algorithms/
│   └── __init__.py              # Recommendation algorithms (to be implemented)
└── utils/
    ├── __init__.py
    └── helpers.py               # Helper utility functions
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd recomsystem
pip install -r requirement.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `recomsystem` directory:

```env
PRODUCT_API_URL=http://localhost:8000
```

Or copy from example:
```bash
cp .env.example .env
```

Then edit `.env` with your Product API URL.

### 3. Run the Service

```bash
python main.py
```

The service will start on `http://localhost:8001`

Or with uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Verify Setup

Check the health endpoint:
```bash
curl http://localhost:8001/api/health
```

Expected response:
```json
{
  "ok": true,
  "service": "Recommendation System",
  "productApiUrl": "http://localhost:8000",
  "productApiConnected": true
}
```

## API Endpoints

### Health Check
- **GET** `/api/health`
- Returns service health and Product API connectivity status

### Root
- **GET** `/`
- Returns service information and available endpoints

## Current Status

✅ **Completed:**
- Project structure setup
- FastAPI application initialization
- Product API client integration
- Basic DTOs (Product, SkinProfile, RecommendationRequest/Response)
- Health check endpoint

🚧 **In Progress / Next Steps:**
- Recommendation algorithm implementation
- Recommendation endpoints (`POST /api/recommendations`, `GET /api/recommendations/quick`)
- Algorithm testing and validation

## Development

### Adding New Algorithms

Place new recommendation algorithms in `algorithms/` directory:

```
algorithms/
├── content_based.py      # Content-based filtering
├── collaborative.py      # Collaborative filtering
└── hybrid.py             # Hybrid approach
```

### Testing

Make sure the Product API service is running before testing:
```bash
# Start Product API (in product/ directory)
cd ../product
python main.py

# In another terminal, start Recommendation service
cd ../recomsystem
python main.py
```

## Dependencies

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **pydantic**: Data validation
- **requests**: HTTP client for Product API
- **python-dotenv**: Environment variable management

## Next Steps

Refer to `IMPLEMENTATION_PLAN.md` for detailed implementation steps.
