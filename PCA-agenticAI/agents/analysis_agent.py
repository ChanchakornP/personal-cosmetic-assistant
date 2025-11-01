"""
LangChain agent for ingredient and skin analysis.
Uses tools to analyze ingredient conflicts and provide safety recommendations.
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
from tools.analysis_tools import analyze_ingredients_tool, check_skin_compatibility_tool
from tools.product_tools import get_product_by_id_tool


def get_analysis_agent():
    """
    Create and return a LangChain agent for ingredient and skin analysis.

    The agent can:
    - Analyze ingredient conflicts between products
    - Check skin compatibility for products
    - Get detailed product information for analysis

    Returns:
        AgentExecutor instance ready to use
    """
    if not llm_service.is_available():
        return None

    # Define tools available to the agent
    tools = [
        analyze_ingredients_tool,
        check_skin_compatibility_tool,
        get_product_by_id_tool,
    ]

    # Create prompt template for the agent
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a cosmetic dermatology expert specializing in ingredient analysis and skin safety.

Your role is to:
1. Analyze ingredient conflicts between cosmetic products
2. Assess skin compatibility for products
3. Provide safety warnings and alternatives when needed

IMPORTANT: Always think step-by-step and show your reasoning process. Use chain-of-thought thinking:

When analyzing ingredients, follow this thinking process:

Step 1 - Understand the Products:
- Identify all products and their key ingredients
- Note the concentration levels (if available)
- Understand the intended use of each product
- Consider the formulation (pH, vehicle, etc.)

Step 2 - Analyze Ingredient Interactions:
- Systematically check for incompatible combinations:
  * Retinol + AHA/BHA (can cause excessive irritation)
  * Niacinamide + Vitamin C at high pH (can cancel each other)
  * Active acids together (over-exfoliation risk)
  * Benzoyl peroxide + retinoids (can be too harsh)
- Think about synergistic combinations (what works well together)
- Consider timing and application order

Step 3 - Assess Skin Compatibility:
- Evaluate against skin type (dry, oily, combination, sensitive, normal)
- Check against specific concerns (acne, aging, sensitivity, etc.)
- Identify potential irritants or allergens
- Consider individual product sensitivity

Step 4 - Reasoning and Risk Assessment:
- Explain the mechanism behind any conflicts
- Assess the severity of potential issues
- Consider mitigation strategies (spacing, timing, dilution)
- Think about alternative approaches

Step 5 - Provide Recommendations:
- Clearly state any conflicts detected
- Explain the reasoning behind your assessment
- Provide specific, actionable alternatives
- Include usage tips and safety warnings

Always show your thinking process clearly. Explain your reasoning step-by-step.
For each conflict or compatibility issue, explain WHY it's a problem and HOW to avoid it.
Always prioritize user safety. Be thorough but clear in your explanations.""",
            ),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    # Create agent
    try:
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
        print(f"Error creating analysis agent: {e}")
        return None
