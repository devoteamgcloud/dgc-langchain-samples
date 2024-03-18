"""LangChain custom output parser utilities."""
import json
from typing import Dict, List, Type, Union

from langchain_core.agents import AgentAction, AgentActionMessageLog, AgentFinish
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.outputs import ChatGeneration, Generation
from langchain_core.pydantic_v1 import BaseModel


class CustomOutputParser(BaseOutputParser):
    """Custom output parser."""

    pydantic_schema: Union[Type[BaseModel], Dict[str, Type[BaseModel]]]

    def parse_result(
        self, result: List[Generation], *, partial: bool = False
    ) -> Union[AgentAction, AgentFinish]:
        """Parse result."""
        if not isinstance(result[0], ChatGeneration):
            raise ValueError("This output parser only works on ChatGeneration output")
        message = result[0].message
        function_call = message.additional_kwargs.get("function_call", {})
        if function_call:
            function_name = function_call["name"]
            tool_input = function_call.get("arguments", {})

            if isinstance(self.pydantic_schema, dict):
                schema = self.pydantic_schema[function_name]
            else:
                schema = self.pydantic_schema

            function_input = schema(**json.loads(tool_input))

            content_msg = f"responded: {message.content}\n" if message.content else "\n"
            log_msg = (
                f"\nInvoking: `{function_name}` with `{tool_input}`\n{content_msg}\n"
            )
            return AgentActionMessageLog(
                tool=function_name,
                tool_input=function_input,
                log=log_msg,
                message_log=[message],
            )

        return AgentFinish(
            return_values={"output": message.content}, log=str(message.content)
        )

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Parse."""
        raise ValueError("Can only parse messages")
