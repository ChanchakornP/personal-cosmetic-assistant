"""
LangChain agent for product recommendations.
Uses tools to search products and provides intelligent recommendations.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.agents import (
    AgentExecutor,
    create_openai_tools_agent,
    create_tool_calling_agent,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from services.llm_service import llm_service
from tools.analysis_tools import check_skin_compatibility_tool
from tools.product_tools import (
    filter_products_by_category_tool,
    filter_products_by_price_tool,
    get_product_by_id_tool,
    search_products_tool,
)


def get_recommendation_agent():
    """
    Create and return a LangChain agent for product recommendations.

    The agent can:
    - Search products by name/description
    - Filter products by category
    - Filter products by price range
    - Check skin compatibility
    - Get detailed product information

    Returns:
        AgentExecutor instance ready to use
    """
    if not llm_service.is_available():
        return None

    # Define tools available to the agent
    tools = [
        search_products_tool,
        get_product_by_id_tool,
        filter_products_by_category_tool,
        filter_products_by_price_tool,
        check_skin_compatibility_tool,
    ]

    # Create prompt template for the agent
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert cosmetic product recommendation assistant. 
Your goal is to help users find the best cosmetic products based on their skin profile.

You have access to tools that let you:
1. Search for products by name or description
2. Filter products by category
3. Filter products by price range
4. Check skin compatibility for products
5. Get detailed product information

IMPORTANT: Always think step-by-step and show your reasoning process. Use chain-of-thought thinking:

When a user asks for recommendations, follow this thinking process:

Step 1 - Understand the Request:
- Analyze the user's skin profile (skin type, concerns, budget, preferred categories)
- Identify key requirements and constraints
- Think about what types of products would address their needs

Step 2 - Plan Your Search Strategy:
- Decide which tools to use first (category filter? price filter? search?)
- Consider the order of operations for efficiency
- Think about how to narrow down the product list

Step 3 - Execute Search and Analysis:
- Use tools to search and filter products
- Evaluate each product against the user's profile
- Check compatibility for promising candidates
- Compare products side-by-side

Step 4 - Reasoning and Evaluation:
- Explain why each product is suitable (or not)
- Consider trade-offs (price vs quality, availability vs preference)
- Rank products based on multiple factors
- Think about potential alternatives

Step 5 - Provide Recommendations:
- Present top recommendations with clear explanations
- Explain the reasoning behind each recommendation
- Mention any important considerations or warnings

Always show your thinking process clearly. Before using a tool, explain why you're using it.
After getting results, analyze them and explain your reasoning.
Be thorough but clear in your explanations.
Focus on products that truly match the user's needs.
Always consider budget constraints and preferred categories when provided.""",
            ),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    # Create agent (using OpenAI-style tools agent, compatible with Gemini tool calling)
    try:
        # Use the LLM from our service
        # Try create_tool_calling_agent first (LangChain 0.2+), fallback to create_openai_tools_agent
        try:
            agent = create_tool_calling_agent(llm_service.llm, tools, prompt)
        except (ImportError, AttributeError):
            # Fallback for older LangChain versions
            agent = create_openai_tools_agent(llm_service.llm, tools, prompt)

        # Create executor with enhanced verbose output for thinking
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
            return_intermediate_steps=True,  # Enable to see thinking steps
        )

        return agent_executor
    except Exception as e:
        print(f"Error creating recommendation agent: {e}")
        return None


# Example usage function
def get_recommendations_with_agent(
    skin_type: str,
    concerns: list,
    budget_range: dict = None,
    preferred_categories: list = None,
    limit: int = 10,
) -> dict:
    """
    Get recommendations using the agent.

    Args:
        skin_type: User's skin type
        concerns: List of skin concerns
        budget_range: Dict with min/max price
        preferred_categories: List of preferred categories
        limit: Number of recommendations

    Returns:
        Dict with recommendations
    """
    agent = get_recommendation_agent()
    if not agent:
        return {"error": "Agent not available"}

    # Build query for the agent
    query_parts = [f"I need product recommendations for {skin_type} skin."]

    if concerns:
        query_parts.append(f"My concerns are: {', '.join(concerns)}.")

    if budget_range:
        min_price = budget_range.get("min", 0)
        max_price = budget_range.get("max", float("inf"))
        if max_price != float("inf"):
            query_parts.append(f"My budget is ${min_price:.2f} - ${max_price:.2f}.")
        else:
            query_parts.append(f"My minimum budget is ${min_price:.2f}.")

    if preferred_categories:
        query_parts.append(
            f"I prefer products in these categories: {', '.join(preferred_categories)}."
        )

    query_parts.append(f"Please provide {limit} top recommendations with explanations.")

    query = " ".join(query_parts)

    try:
        result = agent.invoke({"input": query})
        return {"recommendations": result.get("output", "")}
    except Exception as e:
        return {"error": str(e)}
