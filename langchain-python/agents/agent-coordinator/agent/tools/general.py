"""General utilities for tools."""
from langchain_core.tools import Tool

from agent.tools.knowledge_base import knowledge_base_tool, KnowledgeBaseInput


def get_all_tools(authorization_token: str):
    """Get all tools."""
    return [
        Tool(
            name="knowledge_base_tool",
            description=(
                "A tool to get access to the knowledge base. "
                "Input is the question that must be provided by the user. "
                "Output is the information found in the knowledge base."
            ),
            func=knowledge_base_tool(authorization_token),
            args_schema=KnowledgeBaseInput,
        ),
    ]
