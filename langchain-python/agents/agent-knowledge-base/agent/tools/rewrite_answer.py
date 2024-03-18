"""Rewrite answer tool."""
import os

import google.auth.transport.requests
import google.oauth2.id_token
from langchain_core.pydantic_v1 import BaseModel, Field
from langserve import RemoteRunnable


class RewriteAnswerInput(BaseModel):
    """Rewrite answer input."""

    answer: str = Field(
        description="the answer to rewrite",
    )


def rewrite_answer_tool(authorization_token: str):
    """Rewrite answer."""

    def _wrapper(answer: str):
        cloud_run_id_token = None
        agent_coordinator_url = os.environ.get("_AGENT_COORDINATOR_URL")
        if agent_coordinator_url:
            auth_req = google.auth.transport.requests.Request()
            cloud_run_id_token = google.oauth2.id_token.fetch_id_token(
                auth_req,
                agent_coordinator_url,
            )

        chat = RemoteRunnable(
            agent_coordinator_url or "http://localhost:8080/",
            headers={
                "Authorization": (
                    f"Bearer {cloud_run_id_token}"
                    if cloud_run_id_token
                    else authorization_token
                ),
            },
        )
        answer = chat.invoke(
            {
                "message": f"Please rewrite the following answer to match your personality: {answer}",
                "session_id": "knowledge-base",
            },
        )["output"]
        return answer

    return _wrapper
