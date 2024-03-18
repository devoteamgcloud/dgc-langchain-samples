"""Agent coordinator."""
from typing import Any, Dict, List, Optional, cast

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.prompts.chat import (
    AIMessagePromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.prompts.prompt import PromptTemplate
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import (
    ConfigurableFieldSpec,
    Runnable,
    RunnableConfig,
)
from langchain_core.runnables.utils import Input, Output
from langchain_google_vertexai.chat_models import ChatVertexAI
from unidecode import unidecode
from vertexai.generative_models._generative_models import ResponseBlockedError

from agent.tools.general import get_all_tools
from agent.output_parser import CustomOutputParser


FALLBACK_MESSAGE = (
    "I'm sorry... Unfortunately, I can't help but that. Do you want me "
    "to summarize our exchange and draft a ticket for you?"
)


class InputChat(BaseModel):
    """Input for the chat endpoint."""

    message: str = Field(description="message to send to the agent")


class OutputChat(BaseModel):
    """Output for the chat endpoint."""

    output: str = Field("output from the agent")


def postprocess_output(output: str) -> str:
    """Postprocess output."""
    output = output.strip()
    return output


def simple_responsible_ai_filter(message: str) -> str:
    """Filter message using a simple responsible AI filter."""
    if (
        message == "Agent stopped due to iteration limit or time limit."
        or "```" in message
        or len(message) == 0
        or len(message.split(" ")) < 3
    ):
        return FALLBACK_MESSAGE

    return message


class CustomAgentExecutor(Runnable):
    """A custom runnable that will be used by the agent executor."""

    def __init__(self, **kwargs):
        """Initialize the runnable."""
        super().__init__(**kwargs)

    def invoke(self, input: Input, config: Optional[RunnableConfig] = None) -> Output:
        """Invoke custom agent."""
        configurable = cast(Dict[str, Any], config.pop("configurable", {}))

        tools = get_all_tools(configurable["authorization_token"])
        chat_prompt = ChatPromptTemplate(
            input_variables=[
                "agent_scratchpad",
                "message",
            ],
            messages=[
                HumanMessagePromptTemplate(
                    prompt=PromptTemplate(
                        input_variables=[],
                        template=(
                            "You are a knowledge base. You help users find "
                            "answers to their questions. Before giving an answer "
                            "to the user, you must first rewrite the answer to "
                            "match your personality using your tool. Don't "
                            "ever say that your answer has been rewritten."
                        ),
                    ),
                ),
                AIMessagePromptTemplate(
                    prompt=PromptTemplate(
                        input_variables=[],
                        template=("Understood!"),
                    )
                ),
                HumanMessagePromptTemplate(
                    prompt=PromptTemplate(
                        input_variables=["message"],
                        template="{message}",
                    ),
                ),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ],
        )
        llm = ChatVertexAI(
            model_name="gemini-pro",
            max_output_tokens=8192,
            temperature=0.0,
        )
        llm_with_tools = llm.bind(functions=tools)

        agent = (
            {
                "message": lambda x: unidecode(x["message"]),
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
            }
            | chat_prompt
            | llm_with_tools
            | CustomOutputParser(
                pydantic_schema={tool.name: tool.args_schema for tool in tools},
            )
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=15,
            handle_parsing_errors=FALLBACK_MESSAGE,
            return_intermediate_steps=True,
        )

        remaining_tries = 2
        while remaining_tries > 0:
            answer = None
            try:
                agent_output = agent_executor.invoke(
                    input={
                        "message": unidecode(input["message"]),
                    },
                    config=config,
                )
                answer = postprocess_output(agent_output["output"])
                answer = simple_responsible_ai_filter(answer)
            except ResponseBlockedError:
                answer = FALLBACK_MESSAGE

            if answer != FALLBACK_MESSAGE:
                break

            remaining_tries -= 1

        return {
            "output": answer,
        }

    @property
    def config_specs(self) -> List[ConfigurableFieldSpec]:
        """Get config specs."""
        return [
            ConfigurableFieldSpec(
                id="authorization_token",
                annotation=str,
                name="authorization_token",
                description="authorization token",
            ),
        ]


def get_agent_knowledge_base():
    """Get the agent knowledge base."""
    return CustomAgentExecutor().with_types(
        input_type=InputChat,
        output_type=OutputChat,
    )
