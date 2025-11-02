# Personal Cosmetic Assistant (PCA)

A comprehensive, AI-powered skincare and cosmetic product recommendation platform built with modern technologies and microservices architecture.

## 🎯 Project Overview

PCA is a full-stack application that helps users discover personalized skincare and cosmetic products through intelligent AI-powered recommendations, facial analysis, ingredient conflict detection, and routine tracking.

### Key Features

- **🤖 AI-Powered Recommendations**: LangChain-based agentic AI system using Google Gemini for intelligent product suggestions
- **📸 Facial Analysis**: Analyze skin conditions and concerns through image upload
- **⚠️ Ingredient Conflict Detection**: Check for potentially harmful ingredient combinations
- **📅 Routine Tracker**: Log and track your daily skincare routine with trend analysis
- **🛒 Product Browsing**: Browse and search through an extensive product catalog
- **💳 Payment Integration**: Secure payment processing for purchases
- **🔐 User Authentication**: Secure authentication with Supabase Auth
- **📊 Data Analytics**: Track skincare progress and trends over time

## 🏗️ Architecture

PCA follows a **microservices architecture** with the following components:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│                        TypeScript + Vite                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┬─────────────────┐
    │                │                │                 │
┌───▼─────────┐ ┌───▼────────┐ ┌────▼──────┐ ┌─────────▼──────┐
│   Product   │ │  Payment   │ │ PCA-AI    │ │   Supabase     │
│  Service    │ │  Service   │ │ System    │ │   Database     │
│  (FastAPI)  │ │  (Spring)  │ │ (LangChain│ │   + Storage    │
│             │ │            │ │ + Gemini) │ │   + Auth       │
└─────────────┘ └────────────┘ └───────────┘ └────────────────┘
```

### Service Breakdown

| Service | Technology | Port | Description |
|---------|-----------|------|-------------|
| **Frontend** | React + TypeScript + Vite | 3000 | User interface |
| **Product** | FastAPI (Python) | 8000 | Product catalog |
| **Payment** | Spring Boot (Java) | 8080 | Transactions |
| **PCA-AI** | FastAPI + LangChain + Gemini | 8001 | AI recommendations |
| **Database** | PostgreSQL | 5433 | Payment storage |

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend development)
- pnpm 10+
- Python 3.11+ (for local AI service development)
- Java 17+ (for local payment service development)
- Maven 3.9+ (for payment service)

### Docker Deployment (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/personal-cosmetic-assistant.git
   cd personal-cosmetic-assistant
   ```

2. **Set up environment variables**:
   
   Create `.env` files in each service directory:
   
   **product/.env**:
   ```env
   SUPABASE_URL="your-supabase-url"
   SUPABASE_ANON_KEY="your-supabase-anon-key"
   ```

   **PCA-agenticAI/.env**:
   ```env
   GEMINI_API_KEY="your-gemini-api-key"
   LLM_MODEL="gemini-2.0-flash-exp"
   SUPABASE_URL="your-supabase-url"
   SUPABASE_ANON_KEY="your-supabase-anon-key"
   ```

   **app/.env** (for frontend):
   ```env
   VITE_SUPABASE_URL="your-supabase-url"
   VITE_SUPABASE_ANON_KEY="your-supabase-anon-key"
   ```

3. **Start all services**:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Product API: http://localhost:8000
   - Payment API: http://localhost:8080
   - AI Service: http://localhost:8001
   - API Docs: http://localhost:8000/docs (FastAPI Swagger)

### Local Development

#### Frontend (React)

```bash
cd app
pnpm install
pnpm dev
```

#### Product Service (Python/FastAPI)

```bash
cd product
pip install -r requirement.txt
uvicorn main:app --reload --port 8000
```

#### Payment Service (Java/Spring Boot)

```bash
cd payment
mvn clean install
mvn spring-boot:run
```

#### AI Service (LangChain/Python)

```bash
cd PCA-agenticAI
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

## 🔧 Configuration

### Environment Variables

Each service requires specific environment variables:

#### Frontend (`app/.env`)
```env
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

#### Product Service (`product/.env`)
```env
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
```

#### AI Service (`PCA-agenticAI/.env`)
```env
GEMINI_API_KEY=your-gemini-api-key
LLM_MODEL=gemini-2.0-flash-exp
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
PRODUCT_API_URL=http://localhost:8000  # Optional
```

#### Payment Service (`payment/`)

Configured via Spring Boot's `application.properties`:
```properties
spring.datasource.url=jdbc:postgresql://db:5432/payment
spring.datasource.username=payment_user
spring.datasource.password=payment_password
```

### Supabase Setup

1. Create a Supabase project at https://supabase.com
2. Run migrations from `supabase_migrations/`:
   - `create_facial_analysis_history.sql`
   - `create_skincare_routine_table.sql`
3. Configure RLS policies as needed
4. Enable authentication providers

## 🌐 Deployment

### Production Deployment

The application is containerized and ready for deployment on any Docker-compatible platform:

#### Docker Compose (Single Server)

```bash
docker-compose -f docker-compose.yml up -d
```

#### Individual Services

Each service can be deployed independently:

```bash
# Frontend
cd app && docker build -t pca-webpage . && docker run -p 3000:80 pca-webpage

# Product Service
cd product && docker build -t pca-product . && docker run -p 8000:8000 pca-product

# Payment Service
cd payment && docker build -t pca-payment . && docker run -p 8080:8080 pca-payment

# AI Service
cd PCA-agenticAI && docker build -t pca-agenticai . && docker run -p 8001:8001 pca-agenticai
```

#### Cloud Deployment Options

**Frontend**: Vercel, Netlify, Cloudflare Pages, or any static hosting  
**Backend Services**: AWS ECS, Google Cloud Run, Azure Container Apps, Railway, Render

**Recommended Stack**:
- **Frontend**: Vercel or Netlify
- **Backend Services**: Railway, Render, or Fly.io
- **Database**: Supabase (Managed PostgreSQL)
- **CDN**: Cloudflare

### CI/CD

Each service can be independently deployed with CI/CD:

```yaml
# Example GitHub Actions workflow
name: Deploy PCA Services
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and deploy
        run: docker-compose up -d --build
```

## 🔬 Technology Stack

### Frontend
- **React 19** + **TypeScript** + **Vite** - Modern web development
- **TanStack Query** - Data management and caching
- **Tailwind CSS** - Utility-first styling
- **Supabase JS** - Real-time database and authentication

### Backend Services
- **Product Service**: FastAPI (Python) with Supabase
- **Payment Service**: Spring Boot (Java) with PostgreSQL
- **AI Service**: LangChain + Google Gemini for intelligent recommendations and analysis

### AI Capabilities
- **Recommendation Engine**: Agentic AI with LangChain tools and Chain-of-Thought reasoning
- **Facial Analysis**: Skin condition assessment and concern detection
- **Conflict Detection**: Ingredient compatibility analysis and safety warnings

### Infrastructure
- **Database**: Supabase (PostgreSQL with RLS, JSONB, real-time subscriptions)
- **Storage**: Blob storage for images and facial analysis data
- **Security**: Supabase Auth, Row Level Security, input validation, CORS protection

## 📁 Project Structure

```
personal-cosmetic-assistant/
├── app/                        # Frontend (React + Vite)
│   ├── client/                 # React application
│   │   ├── src/
│   │   │   ├── _core/         # Core functionality
│   │   │   ├── components/    # UI components
│   │   │   ├── contexts/      # React contexts
│   │   │   ├── hooks/         # Custom hooks
│   │   │   ├── lib/          # Utilities
│   │   │   ├── pages/        # Page components
│   │   │   ├── services/     # API services
│   │   │   └── types/        # TypeScript types
│   │   └── public/           # Static assets
│   ├── Dockerfile             # Frontend container
│   └── package.json
│
├── product/                   # Product Service (FastAPI)
│   ├── main.py               # FastAPI application
│   ├── requirement.txt       # Python dependencies
│   ├── Dockerfile
│   └── README.md
│
├── payment/                   # Payment Service (Spring Boot)
│   ├── src/main/java/        # Java source code
│   ├── pom.xml              # Maven configuration
│   ├── Dockerfile
│   └── README.md
│
├── PCA-agenticAI/           # AI Service (LangChain)
│   ├── agents/              # LangChain agents
│   ├── algorithms/          # Recommendation algorithms
│   ├── chains/             # LangChain chains
│   ├── services/           # Core services
│   ├── tools/              # LangChain tools
│   ├── models/             # Data models
│   ├── utils/              # Utilities
│   ├── main.py            # FastAPI application
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── supabase_migrations/     # Database migrations
├── docker-compose.yml       # Docker orchestration
└── README.md               # This file
```

## 🧪 Development

### Running Tests

```bash
# Frontend tests
cd app && pnpm test

# Payment service tests
cd payment && mvn test

# AI service tests (if available)
cd PCA-agenticAI && pytest
```

### Code Quality

```bash
# Frontend linting and formatting
cd app && pnpm format && pnpm check

# Python linting (product & AI services)
pip install black ruff mypy
black product/ PCA-agenticAI/
ruff check product/ PCA-agenticAI/
```

### Database Migrations

```bash
# Run Supabase migrations
# Manually execute SQL files in supabase_migrations/

# Or using Supabase CLI
supabase db push
```

## 📚 API Documentation

### Product Service (FastAPI)
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Payment Service (Spring Boot)
- Health check: http://localhost:8080/actuator/health

### AI Service (FastAPI)
- Swagger UI: http://localhost:8001/docs
- Main endpoints:
  - `POST /api/recommendations` - Get AI recommendations
  - `POST /api/facial-analysis` - Analyze skin image
  - `POST /api/ingredient-conflict` - Check ingredient conflicts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Google Gemini**: For providing the LLM capabilities
- **LangChain**: For the excellent AI application framework
- **Supabase**: For the managed database and authentication
- **Radix UI**: For the accessible component primitives
- **All Contributors**: For their valuable contributions

## 📧 Contact & Support

For questions, issues, or feature requests, please open an issue on GitHub.

---

Built with ❤️ using modern technologies and best practices.
