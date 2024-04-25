"""A conversation with Anthropic Claude."""
from __future__ import annotations
import time
from typing import Any, Callable, TYPE_CHECKING, overload

from anthropic import Anthropic, RateLimitError
from anthropic.types import TextBlockParam
from anthropic.types.beta.tools import (
    ToolParam,
    ToolResultBlockParam,
    ToolsBetaMessage,
    ToolsBetaMessageParam,
)

from .tools.union import UnionSkillSet

if TYPE_CHECKING:
    from .tools import AnthropicTool
    from .tools import ToolResult, ToolSet


class Conversation:
    """A conversation with Anthropic Claude with tools."""

    def __init__(
        self,
        client: Anthropic,
        skills: list[ToolSet] | None = None,
        model: str = "claude-3-haiku-20240307",
        engine: str | None = None,
    ) -> None:
        """Initialize the Conversation class.

        Args:
            client (Anthropic): The Anthropic client.
            skills (list[ToolSet] | None, optional): The list of tool sets to use.
                Defaults to None.
            model (str, optional): The model to use for generating messages.
                Defaults to "claude-3-haiku-20240307".
            engine (str | None, optional): The engine to use. Defaults to None.
        """
        self.client = client
        self.messages: list[ToolsBetaMessageParam] = []
        self.skills = UnionSkillSet(*(skills or []))
        self.model = model
        self.engine = engine

    @property
    def tools_schema(self) -> list[ToolParam]:
        """Get the tools schema.

        Returns:
            list[ToolParam]: The tools schema.
        """
        return self.skills.tools_schema

    def add_message(self, message: ToolsBetaMessageParam | str) -> None:
        """Add a message to the conversation.

        Args:
            message (ToolsBetaMessageParam | str): The message to add.
        """
        if isinstance(message, str):
            self._add_message({"role": "user", "content": message})
        else:
            self._add_message(message)

    def add_messages(self, messages: list[ToolsBetaMessageParam]) -> None:
        """Add multiple messages to the conversation.

        Args:
            messages (list[ToolsBetaMessageParam]): The messages to add.
        """
        for message in messages:
            self.add_message(message)

    def pop_message(self, index: int = -1) -> ToolsBetaMessageParam:
        """Pop a message

        Args:
            index (int): The index. Defaults to -1.

        Returns:
            ToolsBetaMessageParam: The popped message.
        """
        return self.messages.pop(index)

    def clear_messages(self) -> None:
        """Clear all messages from the conversation."""
        self.messages = []

    def _add_message(self, message: ToolsBetaMessageParam) -> None:
        """Add a message to the conversation.

        Args:
            message (ToolsBetaMessageParam): The message to add.
        """
        self.messages.append(message)

    def _generate_message(
        self, retries: int | None = 1, max_tokens: int = 1024
    ) -> ToolsBetaMessage:
        """Generate a message using Anthropic Claude.

        Args:
            retries (int | None, optional): The number of retries. Defaults to 1.
            max_tokens (int, optional): The maximum number of tokens. Defaults to 1024.

        Returns:
            ToolsBetaMessage: The generated message.
        """
        if retries is None:
            retries = -1
        while True:
            try:
                response = self._generate_raw_message(max_tokens=max_tokens)
            except RateLimitError:
                if retries == 0:
                    raise
                retries -= 1
                time.sleep(1)
            else:
                return response

    def _generate_raw_message(self, max_tokens: int = 1024) -> ToolsBetaMessage:
        """Generate a raw message using Anthropic Claude.

        Args:
            max_tokens (int, optional): The maximum number of tokens. Defaults to 1024.

        Returns:
            ToolsBetaMessage: The generated raw message.
        """
        self._merge_same_role_messages()
        return self.client.beta.tools.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            tools=self.tools_schema,
            messages=self.messages,
        )

    def _merge_same_role_messages(self) -> None:
        """Merge messages with the same role if they are adjacent."""
        if not self.messages:
            return
        merged_messages = [self.messages[0]]
        for message in self.messages[1:]:
            if message["role"] == merged_messages[-1]["role"]:
                if isinstance(merged_messages[-1]["content"], str):
                    merged_messages[-1]["content"] = [
                        TextBlockParam(type="text", text=merged_messages[-1]["content"])
                    ]
                if isinstance(message["content"], str):
                    message["content"] = [
                        TextBlockParam(type="text", text=message["content"])
                    ]
                merged_messages[-1]["content"].extend(message["content"])
            else:
                merged_messages.append(message)
        self.messages = merged_messages

    def add_tool_result(self, tool_result: ToolResult) -> bool:
        """Add a tool result to the conversation.

        Args:
            tool_result (ToolResult): The tool result to add.

        Returns:
            bool: True if the tool result was added, False otherwise.
        """
        if tool_result.interpret_return_as_response:
            self.add_message(
                {
                    "role": tool_result.response_role,
                    "content": tool_result.blocks or tool_result.content,
                }
            )
        else:
            self.add_message(
                ToolsBetaMessageParam(
                    role=tool_result.response_role,
                    content=[
                        ToolResultBlockParam(
                            tool_use_id=tool_result.use_id,
                            type="tool_result",
                            content=[
                                TextBlockParam(type="text", text=tool_result.content)
                            ],
                            is_error=False,
                        )
                    ],
                )
            )
        return True

    def run_tool_if_needed(self) -> bool:
        """Run a tool if needed.

        Returns:
            bool: True if a tool was run, False otherwise.
        """
        if not self.messages:
            return False
        last_message = self.messages[-1]
        ran = False
        for block in last_message["content"]:
            if isinstance(block, str):
                continue
            if (block["type"] if isinstance(block, dict) else block.type) == "tool_use":
                # We know that the block is a ToolUseBlockParam
                self.add_tool_result(self.skills.run_tool(input_data=block))  # type: ignore
                ran = True
        return ran

    def generate_message(
        self, retries: int | None = 1, max_tokens=1024
    ) -> ToolsBetaMessageParam:
        """Generate a message using Anthropic Claude.

        Args:
            retries (int | None, optional): The number of retries. Defaults to 1.
            max_tokens (int, optional): The maximum number of tokens. Defaults to 1024.

        Returns:
            ToolsBetaMessageParam: The generated message.
        """
        if self.run_tool_if_needed():
            return self.messages[-1]
        message: ToolsBetaMessage = self._generate_message(retries, max_tokens)
        self.add_message({"role": message.role, "content": message.content})
        return self.messages[-1]

    def _contains_call(self, message: ToolsBetaMessageParam) -> bool:
        """Check if a message contains a tool call.

        Args:
            message (ToolsBetaMessageParam): The message to check.

        Returns:
            bool: True if the message contains a tool call, False otherwise.
        """
        for block in message["content"]:
            if isinstance(block, str):
                continue
            if (block["type"] if isinstance(block, dict) else block.type) in [
                "tool_use",
                "tool_result",
            ]:
                return True
        return False

    def run_until_response(
        self, retries: int | None = 1, max_tokens=1024
    ) -> list[ToolsBetaMessageParam]:
        """Run the conversation until a response is received.

        Args:
            retries (int | None, optional): The number of retries. Defaults to 1.
            max_tokens (int, optional): The maximum number of tokens per message.
                Defaults to 1024.

        Returns:
            list[ToolsBetaMessageParam]: The response messages,
                both from Claude and tools.
        """
        generated = []
        while True:
            message = self.generate_message(retries=retries, max_tokens=max_tokens)
            generated.append(message)
            if not self._contains_call(message):
                return generated

    @overload
    def add_tool(self, tool: AnthropicTool) -> AnthropicTool:
        ...

    @overload
    def add_tool(
        self,
        tool: Callable[..., Any],
        *,
        name: str | None = None,
        description: str | None = None,
        save_return: bool = True,
        serialize: bool = True,
        interpret_as_response: bool = False,
    ) -> Callable[..., Any]:
        ...

    @overload
    def add_tool(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        save_return: bool = True,
        serialize: bool = True,
        interpret_as_response: bool = False,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        ...

    def add_tool(
        self,
        tool: AnthropicTool | Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        save_return: bool = True,
        serialize: bool = True,
        interpret_as_response: bool = False,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]] | Callable[..., Any]:
        """Add a tool to the conversation.

        Args:
            tool (AnthropicTool | Callable[..., Any] | None, optional): The tool to add.
                Defaults to None.
            name (str | None, optional): The name of the tool. Defaults to None.
            description (str | None, optional): The description of the tool.
                Defaults to None.
            save_return (bool, optional): Whether to save the return value of the tool.
                Defaults to True.
            serialize (bool, optional): Whether to serialize the tool. Defaults to True.
            interpret_as_response (bool, optional): Whether to interpret the tool
                as a response. Defaults to False.

        Returns:
            Callable[[Callable[..., Any]], Callable[..., Any]] | Callable[..., Any]:
                The added tool, or a decorator that adds the tool.
        """
        if tool is None:
            return self.skills.add_tool(
                name=name,
                description=description,
                save_return=save_return,
                serialize=serialize,
                interpret_as_response=interpret_as_response,
            )
        return self.skills.add_tool(
            tool,
            name=name,
            description=description,
            save_return=save_return,
            serialize=serialize,
            interpret_as_response=interpret_as_response,
        )

    def remove_tool(self, tool: str | AnthropicTool | Callable[..., Any]) -> None:
        """Remove a tool from the conversation.

        Args:
            tool (str | AnthropicTool | Callable[..., Any]): The tool to remove.
        """
        self.skills.remove_tool(tool)

    def ask(
        self, question: str, retries: int | None = 1, max_tokens: int = 1024
    ) -> list[ToolsBetaMessageParam]:
        """Ask a question to Anthropic Claude.

        Args:
            question (str): The question to ask.
            retries (int | None, optional): The number of retries. Defaults to 1.
            max_tokens (int, optional): The maximum number of tokens per message.
                Defaults to 1024.

        Returns:
            The response to the question.
        """
        self.add_message(question)
        return self.run_until_response(retries=retries, max_tokens=max_tokens)

    def add_skill(self, skill: ToolSet) -> None:
        """Add a skill to the conversation.

        Args:
            skill (ToolSet): The skill to add.
        """
        self.skills.add_skill(skill)
