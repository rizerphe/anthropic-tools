"""A skill set that combines multiple tool sets."""
from __future__ import annotations
import contextlib
from typing import TYPE_CHECKING

from anthropic.types.beta.tools import ToolParam, ToolUseBlock, ToolUseBlockParam

from ..exceptions import ToolNotFoundError
from .basic_set import BasicToolSet

if TYPE_CHECKING:
    from .tools import ToolResult
    from .sets import ToolSet


class UnionSkillSet(BasicToolSet):
    """A skill set that combines multiple tool sets."""

    def __init__(self, *sets: ToolSet) -> None:
        """Initialize the UnionSkillSet.

        Args:
            sets: The tool sets to be combined.
        """
        self.sets = list(sets)
        super().__init__()

    @property
    def tools_schema(self) -> list[ToolParam]:
        """Get the schema of the tools in the skill set.

        Returns:
            The list of tool parameters.
        """
        return super().tools_schema + sum(
            (tool_set.tools_schema for tool_set in self.sets), []
        )

    def run_tool(self, input_data: ToolUseBlock | ToolUseBlockParam) -> ToolResult:
        """Run a tool using the skill set.

        Args:
            input_data: The input data for the tool.

        Returns:
            The result of running the tool.
        """
        for tool_set in self.sets:
            with contextlib.suppress(ToolNotFoundError):
                return tool_set.run_tool(input_data)
        return super().run_tool(input_data)

    def add_skill(self, skill: ToolSet) -> None:
        """Add a tool set to the skill set.

        Args:
            skill: The tool set to be added.
        """
        self.sets.append(skill)
