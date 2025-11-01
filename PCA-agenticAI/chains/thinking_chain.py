"""
Chain-of-thought thinking utilities for agents.
Provides structured reasoning chains for better AI decision-making.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from services.llm_service import llm_service

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class ThinkingChain:
    """
    Chain-of-thought thinking chain for structured reasoning.
    Helps agents reason through problems step-by-step.
    """

    def __init__(self, system_prompt: Optional[str] = None):
        """
        Initialize thinking chain.

        Args:
            system_prompt: Optional system prompt to guide thinking
        """
        if not LANGCHAIN_AVAILABLE or not llm_service.is_available():
            self.available = False
            return

        self.available = True
        self.llm = llm_service.llm

        default_system = """You are a thinking assistant. Break down problems into clear, logical steps.
Think step-by-step and show your reasoning process clearly.
Always explain WHY before proposing WHAT."""

        self.system_prompt = system_prompt or default_system

        # Create the thinking chain
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                (
                    "human",
                    """Let's think through this problem step by step:

Problem: {problem}

Please provide your reasoning in the following format:

Step 1 - [Understanding/Analysis]:
[Your thoughts]

Step 2 - [Planning/Strategy]:
[Your approach]

Step 3 - [Execution/Action]:
[What you would do]

Step 4 - [Reasoning/Evaluation]:
[Why this approach works]

Step 5 - [Conclusion/Recommendation]:
[Your conclusion]

Provide clear, structured reasoning.""",
                ),
            ]
        )

        self.chain = self.prompt | self.llm | StrOutputParser()

    def think(
        self,
        problem: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Perform chain-of-thought thinking on a problem.

        Args:
            problem: The problem or question to think about
            context: Optional context information
            temperature: Temperature for thinking (default: 0.7)

        Returns:
            Structured thinking/reasoning output
        """
        if not self.available:
            return f"Thinking chain not available. Problem: {problem}"

        # Build full problem statement
        problem_text = problem
        if context:
            context_text = "\n".join([f"- {k}: {v}" for k, v in context.items()])
            problem_text = f"{problem}\n\nContext:\n{context_text}"

        try:
            # Use a temporary LLM instance with custom temperature
            import os

            from langchain_google_genai import ChatGoogleGenerativeAI

            thinking_llm = ChatGoogleGenerativeAI(
                model=llm_service.model,
                google_api_key=os.getenv("GEMINI_API_KEY"),
                temperature=temperature,
            )

            thinking_chain = self.prompt | thinking_llm | StrOutputParser()
            result = thinking_chain.invoke({"problem": problem_text})
            return result
        except Exception as e:
            return f"Error in thinking chain: {str(e)}"

    def structured_thinking(
        self,
        steps: List[str],
        problem: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """
        Perform structured thinking with predefined steps.

        Args:
            steps: List of step names/descriptions
            problem: The problem to think about
            context: Optional context information

        Returns:
            Dictionary mapping step names to reasoning
        """
        if not self.available:
            return {step: "Thinking not available" for step in steps}

        # Create a custom prompt for structured thinking
        steps_text = "\n".join(
            [f"Step {i+1} - {step}:" for i, step in enumerate(steps)]
        )

        structured_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                (
                    "human",
                    f"""Let's think through this problem systematically:

Problem: {problem}
{f"Context: {context}" if context else ""}

Please provide reasoning for each step:

{steps_text}

Provide clear, structured reasoning for each step.""",
                ),
            ]
        )

        try:
            import os

            from langchain_google_genai import ChatGoogleGenerativeAI

            thinking_llm = ChatGoogleGenerativeAI(
                model=llm_service.model,
                google_api_key=os.getenv("GEMINI_API_KEY"),
                temperature=0.7,
            )

            chain = structured_prompt | thinking_llm | StrOutputParser()
            result = chain.invoke({"problem": problem, "context": context or {}})

            # Parse result into steps (basic parsing)
            thinking_steps = {}
            current_step = None
            current_text = []

            for line in result.split("\n"):
                if line.strip().startswith("Step") and ":" in line:
                    if current_step:
                        thinking_steps[current_step] = "\n".join(current_text).strip()
                    # Extract step name
                    step_name = line.split(":", 1)[0].strip()
                    current_step = step_name
                    current_text = []
                elif current_step:
                    current_text.append(line)

            if current_step:
                thinking_steps[current_step] = "\n".join(current_text).strip()

            return thinking_steps
        except Exception as e:
            return {step: f"Error: {str(e)}" for step in steps}


def create_thinking_chain(
    system_prompt: Optional[str] = None,
) -> Optional[ThinkingChain]:
    """
    Create a thinking chain instance.

    Args:
        system_prompt: Optional system prompt

    Returns:
        ThinkingChain instance or None if not available
    """
    if not LANGCHAIN_AVAILABLE or not llm_service.is_available():
        return None

    return ThinkingChain(system_prompt=system_prompt)
