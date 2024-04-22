"""A basic set of tools."""
from __future__ import annotations

from anthropic.types.beta.tools import ToolParam, ToolUseBlock, ToolUseBlockParam

from anthropic_tools.json_type import JsonType

from ..exceptions import BrokenSchemaError, ToolNotFoundError
from .sets import MutableToolSet
from .tools import AnthropicTool, RawToolResult, ToolResult


class BasicToolSet(MutableToolSet):
    """A basic set of tools."""

    def __init__(self, tools: list[AnthropicTool] | None = None) -> None:
        """Initialize the BasicToolSet.

        Args:
            tools: A list of AnthropicTool objects. Defaults to None.
        """
        self.tools = tools or []

    @property
    def tools_schema(self) -> list[ToolParam]:
        """Get the schema of all tools in the set, in the format the API expects.

        Returns:
            A list of ToolParam objects representing the schema of each tool.
        """
        return [tool.schema for tool in self.tools]

    def run_tool(self, input_data: ToolUseBlock | ToolUseBlockParam) -> ToolResult:
        """Run a tool with the given input data.

        Args:
            input_data: The input data for the tool,
                either as a ToolUseBlock or ToolUseBlockParam object.

        Returns:
            A ToolResult object representing the result of running the tool.

        Raises:
            BrokenSchemaError: If the input data does not match the tool's schema.
        """
        tool = self.find_tool(
            input_data["name"] if isinstance(input_data, dict) else input_data.name
        )
        arguments = (
            input_data["input"] if isinstance(input_data, dict) else input_data.input
        )
        if not isinstance(arguments, dict):
            raise BrokenSchemaError(arguments, tool.schema["input_schema"])
        result = self.get_tool_result(tool, arguments)
        return ToolResult(
            input_data["id"] if isinstance(input_data, dict) else input_data.id,
            tool.name,
            result,
            tool.interpret_as_response,
        )

    def find_tool(self, tool_name: str) -> AnthropicTool:
        """Find a tool by its name.

        Args:
            tool_name: The name of the tool to find.

        Returns:
            The AnthropicTool object with the specified name.

        Raises:
            ToolNotFoundError: If the tool with the specified name is not found.
        """
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        raise ToolNotFoundError(tool_name)

    def get_tool_result(
        self, tool: AnthropicTool, arguments: dict[str, JsonType]
    ) -> RawToolResult | None:
        """Get the result of running a tool with the given arguments.

        Args:
            tool: The AnthropicTool object representing the tool to run.
            arguments: The arguments for the tool.

        Returns:
            A RawToolResult object representing the result of running the tool,
                or None if the tool does not save the return value.
        """
        result = tool(arguments)
        if tool.save_return:
            return RawToolResult(result, serialize=tool.serialize)
        return None

    def _add_tool(self, tool: AnthropicTool) -> None:
        """Add a tool to the set.

        Args:
            tool: The AnthropicTool object representing the tool to add.
        """
        self.tools.append(tool)

    def _remove_tool(self, name: str) -> None:
        """Remove a tool from the set by its name.

        Args:
            name: The name of the tool to remove.
        """
        self.tools = [f for f in self.tools if f.name != name]
