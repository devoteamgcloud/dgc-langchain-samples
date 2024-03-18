"""Agent coordinator."""
from typing import Any, Dict, List, Optional, cast

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.memory import ConversationSummaryBufferMemory
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
from agent.history import get_session_history, put_session_data
from agent.output_parser import CustomOutputParser


FALLBACK_MESSAGE = (
    "I'm sorry... Unfortunately, I can't help but that. Do you want me "
    "to summarize our exchange and draft a ticket for you?"
)


class InputChat(BaseModel):
    """Input for the chat endpoint."""

    message: str = Field(description="message to send to the agent")
    session_id: str = Field(description="session id")


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
                "chat_history",
                "message",
            ],
            messages=[
                HumanMessagePromptTemplate(
                    prompt=PromptTemplate(
                        input_variables=[],
                        template=(
                            "Your job is to help employees find answers to questions "
                            "using your knowledge base. You should always use the "
                            "knowledge base tool.\n"
                            "You are very open, friendly, and sassy. You are always "
                            "polite and professional, never aggressive. You must "
                            "always be helpful and exhaustive. Make employees feel "
                            "at ease.\n"
                            "Whenever you are asked to rewrite an answer, you must "
                            "rewrite the answer exactly as it is written, but in "
                            "your own words to match your personality. In this case, "
                            "only answer with the rewritten version."
                        ),
                    ),
                ),
                AIMessagePromptTemplate(
                    prompt=PromptTemplate(
                        input_variables=[],
                        template=("Understood!"),
                    )
                ),
                MessagesPlaceholder(variable_name="chat_history"),
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
                "chat_history": lambda x: x["chat_history"],
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

        history, session_conversation = get_session_history(
            session_id=input["session_id"],
        )
        memory = ConversationSummaryBufferMemory(
            llm=llm,
            max_token_limit=8192,
            chat_memory=history,
            memory_key="chat_history",
            output_key="output",
            return_messages=True,
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            max_iterations=15,
            handle_parsing_errors=FALLBACK_MESSAGE,
            return_intermediate_steps=True,
        )

        remaining_tries = 2
        while remaining_tries > 0:
            function_messages = []
            answer = None
            try:
                agent_output = agent_executor.invoke(
                    input={
                        "message": unidecode(input["message"]),
                    },
                    config=config,
                )
                function_messages = format_to_openai_function_messages(
                    agent_output["intermediate_steps"]
                )
                answer = postprocess_output(agent_output["output"])
                answer = simple_responsible_ai_filter(answer)
            except ResponseBlockedError:
                answer = FALLBACK_MESSAGE

            if answer != FALLBACK_MESSAGE:
                break

            remaining_tries -= 1

        put_session_data(
            session_conversation,
            input["message"],
            function_messages,
            answer,
            input["session_id"],
        )

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


def get_agent_coordinator():
    """Get the agent coordinator."""
    return CustomAgentExecutor().with_types(
        input_type=InputChat,
        output_type=OutputChat,
    )
