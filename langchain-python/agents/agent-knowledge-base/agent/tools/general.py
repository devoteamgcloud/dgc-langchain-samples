"""General utilities for tools."""
from langchain_core.tools import Tool

from agent.tools.rewrite_answer import rewrite_answer_tool, RewriteAnswerInput


def get_all_tools(authorization_token: str):
    """Get all tools."""
    return [
        Tool(
            name="rewrite_answer_tool",
            description=(
                "A tool to rewrite your answers before sending them to the user. "
                "Input is your answer. "
                "Output is the rewritten answer."
            ),
            func=rewrite_answer_tool(authorization_token),
            args_schema=RewriteAnswerInput,
        ),
    ]
