"""Datastore utilities."""
from datetime import datetime
from functools import lru_cache
import json
import os
from typing import List

from google.cloud import datastore
from langchain.memory import ChatMessageHistory
from langchain_core.messages import AIMessageChunk, BaseMessage, FunctionMessage


PROJECT_ID = os.environ.get("_PROJECT_ID", "dgc-ml-gemini-autogen")
DATASTORE_SESSION_ENTITY_NAME = os.environ.get(
    "_DATASTORE_SESSION_ENTITY_NAME", "session"
)


@lru_cache(1)
def get_datastore_client() -> datastore.Client:
    """Get a Datastore client."""
    return datastore.Client(project=PROJECT_ID)


LOCAL_DATABASE = {}


def get_from_database(session_id: str):
    """Get session from database."""
    session = None
    if os.environ.get("_LOCAL"):
        print(LOCAL_DATABASE)
        session = LOCAL_DATABASE.get(session_id)
    else:
        ds_client = get_datastore_client()
        key = ds_client.key(DATASTORE_SESSION_ENTITY_NAME, session_id)
        session = ds_client.get(key)

    return session


def put_in_database(session_id, value):
    """Put in database."""
    if os.environ.get("_LOCAL"):
        print(LOCAL_DATABASE)
        LOCAL_DATABASE[session_id] = value
    else:
        ds_client = get_datastore_client()
        key = ds_client.key(
            DATASTORE_SESSION_ENTITY_NAME,
            session_id,
        )
        session = datastore.Entity(
            key,
            exclude_from_indexes=[
                "conversation",
            ],
        )
        session.update(value)
        ds_client.put(session)


def get_session_history(session_id: str) -> ChatMessageHistory:
    """Get session history."""
    history = ChatMessageHistory()
    if session_id == "knowledge-base":
        return history, []

    session = get_from_database(session_id)
    if session is None:
        return history, []

    for interaction in session["conversation"]:
        history.add_user_message(interaction["question"])
        if "tools" in interaction:
            if isinstance(interaction["tools"], str):
                interaction["tools"] = json.loads(interaction["tools"])

            if not isinstance(interaction["tools"], str):
                for msg in interaction["tools"]:
                    if msg["type"] == "AIMessageChunk":
                        history.messages.append(AIMessageChunk(**msg))
                    elif msg["type"] == "function":
                        history.messages.append(FunctionMessage(**msg))
        history.add_ai_message(interaction["answer"])

    return history, session["conversation"]


def put_session_data(
    session_conversation: List[dict],
    question: str,
    function_messages: List[BaseMessage],
    answer: str,
    session_id: str,
):
    """Put session data in Datastore."""
    if session_id == "knowledge-base":
        return

    conversation = []

    interactions = session_conversation.copy()
    interactions.append(
        {
            "question": question,
            "answer": answer,
            "tools": [m.dict() for m in function_messages],
        }
    )
    for interaction in interactions:
        value = {
            "question": interaction["question"],
            "answer": interaction["answer"],
            "tools": (
                interaction["tools"]
                if isinstance(interaction["tools"], (str, list))
                else json.dumps(interaction["tools"])
            ),
        }
        if not os.environ.get("_LOCAL"):
            qa = datastore.Entity(exclude_from_indexes=["question", "answer", "tools"])
            qa.update(value)
            value = qa

        conversation.append(value)

    put_in_database(
        session_id,
        {
            "conversation": conversation,
            "last_message_utc": datetime.utcnow(),
        },
    )
