"""Berry RAG agent."""
import os
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from langserve import add_routes

from agent.coordinator import get_agent_coordinator


PORT = int(os.getenv("AIP_HTTP_PORT", "8080"))


app = FastAPI(
    title="Demo agent coordinator",
    description="This is a demo agent to coordinate multiple agents together.",
    version="1.0.0",
)


def per_req_config_modifier(config: Dict, request: Request) -> Dict:
    """Modify the config for each request."""
    config["configurable"] = {}
    authorization_token = request.headers.get("authorization")
    if authorization_token:
        config["configurable"]["authorization_token"] = authorization_token
    else:
        raise HTTPException(403, "Invalid authorization token")

    return config


add_routes(
    app,
    get_agent_coordinator(),
    per_req_config_modifier=per_req_config_modifier,
    enabled_endpoints=["invoke"],
)


if __name__ == "__main__":
    import uvicorn

    os.environ.update(
        {
            "_LOCAL": "1",
        }
    )

    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # nosec - Listen to all interfaces
        port=PORT,
        reload=True,
    )
