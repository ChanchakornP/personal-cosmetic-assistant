# PCA AgenticAI System

LangChain-powered agentic AI system for cosmetic product recommendations.

## Overview

This module migrates the recommendation system from direct Gemini API calls to a LangChain-based agentic AI architecture. The system uses:

- **LangChain** for orchestration and agent management
- **Google Gemini** (via LangChain) for LLM capabilities
- **LangChain Tools** for product search, filtering, and analysis
- **LangChain Agents** for intelligent recommendation and analysis workflows
- **Traditional algorithms** (content-based, popularity, hybrid) for product ranking
- **Supabase** for product data access

## Features

### Agentic AI Capabilities

1. **Recommendation Agent**: Intelligent product search and recommendation with tool usage
2. **Analysis Agent**: Ingredient conflict analysis and skin compatibility checking
3. **LangChain Tools**: Reusable tools for product operations
4. **Chain-of-Thought Thinking**: Step-by-step reasoning process for transparent decision-making

### Key Components

- `services/llm_service.py`: LangChain-based LLM service using Gemini
- `agents/`: LangChain agents for recommendations and analysis
- `tools/`: LangChain tools for product operations
- `algorithms/`: Traditional recommendation algorithms (content-based, popularity, hybrid)
- `services/recommendation_engine.py`: Orchestrates algorithms and LLM explanations

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `env.example` to `.env` and fill in your credentials:

```bash
cp env.example .env
```

Required environment variables:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anon key

Optional:
- `LLM_MODEL`: Model to use (default: `gemini-2.0-flash-exp`)
- `PRODUCT_API_URL`: Product API URL if not using Supabase directly

### 3. Run the Service

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Production
uvicorn main:app --host 0.0.0.0 --port 8001
```

Or using Docker:

```bash
docker build -t pca-agenticai .
docker run -p 8001:8001 --env-file .env pca-agenticai
```

## API Endpoints

All endpoints match the original recomsystem API for compatibility:

- `GET /`: Service information
- `GET /api/health`: Health check
- `POST /api/recommendations`: Get personalized recommendations
- `GET /api/recommendations/quick`: Quick recommendations (query params)
- `POST /api/facial-analysis`: Analyze facial image and get recommendations
- `POST /api/ingredient-conflict`: Analyze ingredient conflicts

## Architecture

### LangChain Integration

The system uses LangChain for:

1. **LLM Abstraction**: `ChatGoogleGenerativeAI` for Gemini integration
2. **Tool Management**: Structured tools for product operations
3. **Agent Orchestration**: Agents that can use tools to complete tasks
4. **Prompt Templates**: Reusable prompts for consistent AI behavior
5. **Chain-of-Thought Thinking**: Structured reasoning chains for transparent decision-making

### Chain-of-Thought Thinking

The system implements chain-of-thought (CoT) thinking to make agent reasoning transparent and structured:

- **Step-by-Step Reasoning**: Agents break down problems into clear steps
- **Explicit Thinking Process**: Each agent shows its reasoning before taking action
- **Structured Analysis**: Problems are analyzed systematically (Understand → Plan → Execute → Evaluate → Conclude)
- **Thinking Chain Utility**: Reusable `ThinkingChain` class for structured reasoning

The recommendation agent follows this thinking process:
1. **Understand**: Analyze user's skin profile and requirements
2. **Plan**: Decide search strategy and tool usage order
3. **Execute**: Search and filter products using tools
4. **Reason**: Evaluate products and explain why they match
5. **Recommend**: Provide top recommendations with clear explanations

The analysis agent follows this thinking process:
1. **Understand**: Identify products and key ingredients
2. **Analyze**: Check for incompatible ingredient combinations
3. **Assess**: Evaluate skin compatibility
4. **Reason**: Explain mechanisms and assess risks
5. **Recommend**: Provide safety warnings and alternatives

### Migration from Recomsystem

Key differences from the original recomsystem:

- ✅ Uses LangChain instead of direct Gemini API calls
- ✅ Implements agentic AI with tools and agents
- ✅ Maintains API compatibility
- ✅ Enhanced with structured tool usage
- ✅ Better error handling and retry logic through LangChain

### Components Structure

```
PCA-agenticAI/
├── agents/              # LangChain agents
│   ├── recommendation_agent.py
│   └── analysis_agent.py
├── chains/              # LangChain chains for thinking
│   └── thinking_chain.py
├── tools/               # LangChain tools
│   ├── product_tools.py
│   └── analysis_tools.py
├── services/           # Core services
│   ├── llm_service.py  # LangChain LLM service
│   ├── recommendation_engine.py
│   ├── supabase_client.py
│   └── product_client.py
├── algorithms/         # Recommendation algorithms
│   ├── content_based.py
│   ├── popularity.py
│   └── hybrid.py
├── models/            # Data models
│   └── dtos.py
├── utils/             # Utilities
│   └── helpers.py
└── main.py            # FastAPI application
```

## Usage Example

### Basic Agent Usage

```python
from services.llm_service import llm_service
from agents.recommendation_agent import get_recommendation_agent

# Check if service is available
if llm_service.is_available():
    # Use the recommendation agent with chain-of-thought thinking
    agent = get_recommendation_agent()
    if agent:
        result = agent.invoke({
            "input": "I need recommendations for oily skin with acne concerns, budget $20-50"
        })
        print(result)
        # Result includes intermediate_steps showing the thinking process
        if "intermediate_steps" in result:
            print("Thinking steps:", result["intermediate_steps"])
```

### Using Thinking Chain

```python
from chains.thinking_chain import create_thinking_chain

# Create a thinking chain
thinking = create_thinking_chain()

if thinking:
    # Perform structured thinking
    result = thinking.think(
        problem="Which products work best for sensitive skin with aging concerns?",
        context={"budget": "$30-60", "preferred_categories": ["serum", "moisturizer"]}
    )
    print(result)
    
    # Or use structured thinking with predefined steps
    steps = [
        "Understanding skin requirements",
        "Analyzing product compatibility",
        "Evaluating budget constraints",
        "Making final recommendations"
    ]
    structured_result = thinking.structured_thinking(steps, problem)
    print(structured_result)
```

## Development

### Adding New Tools

1. Create tool in `tools/` directory using `@tool` decorator
2. Add tool to agent's tool list in `agents/`
3. Update `tools/__init__.py`

### Adding New Agents

1. Create agent in `agents/` directory
2. Define tools and prompt template
3. Use `create_openai_tools_agent` to create agent
4. Return `AgentExecutor` instance

## Troubleshooting

### LLM Service Not Available

- Check `GEMINI_API_KEY` is set correctly
- Verify `langchain-google-genai` is installed
- Check model name is valid

### Agent Creation Fails

- Ensure all required tools are properly defined
- Check LangChain version compatibility
- Verify LLM service is initialized

### Supabase Connection Issues

- Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY` are correct
- Check network connectivity
- Verify table structure matches expected schema

## License

Same as parent project.

