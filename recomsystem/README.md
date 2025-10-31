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
# Supabase Configuration (REQUIRED)
SUPABASE_URL=your_url_here
SUPABASE_ANON_KEY=your_anon_key_here

# Gemini LLM Configuration (OPTIONAL - for AI-powered explanations)
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-1.5-flash
```

**Where to find your Supabase credentials:**
1. Go to your Supabase project dashboard
2. Navigate to Settings → API
3. Copy the "Project URL" for `SUPABASE_URL`
4. Copy the "anon public" key for `SUPABASE_ANON_KEY`

**Note:** The Supabase credentials are required for the system to connect to your database.

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
- **Content-based recommendation algorithm** with scoring system
- **Recommendation endpoints** (`POST /api/recommendations`, `GET /api/recommendations/quick`)
- Recommendation engine service

## API Endpoints

### Health Check
- **GET** `/api/health`
- Returns service health and Product API connectivity status

### Get Recommendations (Full)
- **POST** `/api/recommendations`
- Request body:
  ```json
  {
    "skinProfile": {
      "skinType": "dry",
      "concerns": ["dryness", "aging"],
      "preferredCategories": ["Moisturizer", "Serum"],
      "budgetRange": {
        "min": 10,
        "max": 50
      },
      "excludeProducts": [1, 2]
    },
    "limit": 10,
    "strategy": "hybrid"
  }
  ```
- Response:
  ```json
  {
    "products": [...],
    "count": 10,
    "reasons": {
      "5": ["Matches your preferred category: Moisturizer", "Suitable for dry skin"]
    }
  }
  ```

### Quick Recommendations
- **GET** `/api/recommendations/quick?skinType=dry&category=Moisturizer&strategy=hybrid&limit=10`
- Query parameters:
  - `skinType`: dry, oily, combination, sensitive, normal
  - `category`: Product category
  - `strategy`: `content` | `popularity` | `hybrid` (default)
  - `limit`: Number of recommendations (1-50, default: 10)

## How It Works

### Scoring Algorithm

The recommendation system uses a rule-based scoring approach:

1. **Base Score**: 50 points
2. **Category Match**: +25 points (if in preferred categories)
3. **Price in Budget**: +20 points
4. **Price Above Budget**: -30 points
5. **Skin Type Match**: +15 points (keyword matching in description)
6. **Concern Match**: +10 points per matched concern
7. **Stock Availability**: +5 if in stock, -50 if out of stock

Products are ranked by score and top N recommendations are returned with explanations.

### Algorithms

- **content**: Rule-based content matching using keywords, categories, budget, and stock.
- **popularity**: Heuristics favoring in-stock, affordable, frequent-category, and recent products.
- **hybrid**: Weighted blend of content and popularity (default: 70% content, 30% popularity).

### Matching Logic

- **Skin Type Matching**: Searches product name and description for keywords related to the skin type (e.g., "hydrating", "moisturizing" for dry skin)
- **Concern Matching**: Matches user concerns (acne, aging, etc.) with product descriptions
- **Category Filtering**: Prioritizes products from preferred categories
- **Budget Filtering**: Filters and scores products based on price range

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
