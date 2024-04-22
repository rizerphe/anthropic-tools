"""Protocols for the sets of tools used by Anthropic Claude."""
from __future__ import annotations
from functools import partial
from typing import Any, Callable, Protocol, TYPE_CHECKING, overload

from anthropic.types.beta.tools import ToolParam, ToolUseBlock, ToolUseBlockParam

from .tools import AnthropicTool, ToolResult
from .wrapper import ToolWrapper, WrapperConfig

if TYPE_CHECKING:
    from ..json_type import JsonType


class ToolSet(Protocol):
    """A protocol defining a set of tools that can be used by Anthropic Claude."""

    @property
    def tools_schema(self) -> list[ToolParam]:
        """Get the schema of the tools in the set."""
        ...  # pylint: disable=unnecessary-ellipsis

    def run_tool(self, input_data: ToolUseBlock | ToolUseBlockParam) -> ToolResult:
        """Run a tool from the set with the given input data.

        Args:
            input_data: The input data for the tool.
        """
        ...  # pylint: disable=unnecessary-ellipsis

    def __call__(self, input_data: ToolUseBlock | ToolUseBlockParam) -> JsonType:
        """Call the tool set with the given input data.

        Args:
            input_data: The input data for the tool.

        Returns:
            The result of running the tool.
        """
        return self.run_tool(input_data).result


class MutableToolSet(ToolSet, Protocol):
    """A protocol defining a mutable set of tools that can be used by Anthropic Claude."""

    def _add_tool(self, tool: AnthropicTool) -> None:
        """Add a tool to the set.

        Args:
            tool: The tool to add.
        """
        ...  # pylint: disable=unnecessary-ellipsis

    @overload
    def add_tool(self, tool: AnthropicTool) -> AnthropicTool:
        ...  # pylint: disable=unnecessary-ellipsis

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
        ...  # pylint: disable=unnecessary-ellipsis

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
        ...  # pylint: disable=unnecessary-ellipsis

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
        """Add a tool to the set.

        Args:
            tool: The tool to add.
            name: The name of the tool.
            description: The description of the tool.
            save_return: Whether to save the return value of the tool.
            serialize: Whether to serialize the return value of the tool.
            interpret_as_response: Whether to interpret the return value as a response.

        Returns:
            The added tool or a decorator to add a callable tool.
        """
        if isinstance(tool, AnthropicTool):
            self._add_tool(tool)
            return tool
        if callable(tool):
            self._add_tool(
                ToolWrapper(
                    tool,
                    WrapperConfig(None, save_return, serialize, interpret_as_response),
                    name=name,
                    description=description,
                )
            )
            return tool
        return partial(
            self.add_tool,
            name=name,
            description=description,
            save_return=save_return,
            serialize=serialize,
            interpret_as_response=interpret_as_response,
        )

    def remove_tool(self, tool: str | AnthropicTool | Callable[..., Any]) -> None:
        """Remove a tool from the set.

        Args:
            tool: The tool to remove. It can be the name of the tool,
                an AnthropicTool, or a callable.
        """
        if isinstance(tool, str):
            self._remove_tool(tool)
            return
        if isinstance(tool, AnthropicTool):
            self._remove_tool(tool.name)
            return
        self._remove_tool(tool.__name__)

    def _remove_tool(self, name: str) -> None:
        ...
