"""A definition of a tool set that can be used by Anthropic Claude."""
from __future__ import annotations
from dataclasses import dataclass
import json
from typing import Any, Iterable, Literal, Protocol, TYPE_CHECKING, runtime_checkable

from anthropic.types import ImageBlockParam, TextBlockParam
from anthropic.types.beta.tools import (
    ToolResultBlockParam,
    ToolUseBlockParam,
    ToolsBetaContentBlock,
)

from ..exceptions import NonSerializableOutputError

if TYPE_CHECKING:
    from anthropic.types.beta.tools import ToolParam
    from ..json_type import JsonType


@runtime_checkable
class AnthropicTool(Protocol):
    """Protocol for Anthropic Tools.

    Anthropic Tools are callable objects that can be used by Anthropic Claude,
    what sets them apart from a regular function is that they have a schema.
    """

    def __call__(self, arguments: dict[str, JsonType]) -> Any:
        """Call the Anthropic Tool with the given arguments.

        Args:
            arguments: A dictionary of arguments to be passed to the Anthropic Tool.

        Returns:
            The result of the Anthropic Tool.

        Raises:
            Any exception raised by the Anthropic Tool.
        """

    @property
    def schema(self) -> ToolParam:
        """Get the schema of the Anthropic Tool.

        Returns:
            The schema of the Anthropic Tool.
        """
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def name(self) -> str:
        """Get the name of the Tool.

        Returns:
            The name of the Tool.
        """
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def save_return(self) -> bool:
        """Check if the return value of the Tool should be added to the convo."""
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def serialize(self) -> bool:
        """Check if the return value of the Tool should be serialized."""
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def interpret_as_response(self) -> bool:
        """Check if the return value of the Anthropic Tool should be interpreted as
        the assistant's response.
        """
        ...  # pylint: disable=unnecessary-ellipsis


@dataclass
class RawToolResult:
    """The raw result of an Anthropic Tool.

    The raw result can be serialized and converted to content blocks.
    """

    result: Any
    serialize: bool = True

    @property
    def serialized(self) -> str:
        """Serialize the raw result.

        Returns:
            The serialized raw result.

        Raises:
            NonSerializableOutputError: If the raw result cannot be serialized.
        """
        if self.serialize:
            try:
                return json.dumps(self.result, indent=2)
            except TypeError as error:
                raise NonSerializableOutputError(self.result) from error
        return str(self.result)

    @property
    def as_content(
        self,
    ) -> (
        str
        | Iterable[
            ToolsBetaContentBlock
            | TextBlockParam
            | ImageBlockParam
            | ToolUseBlockParam
            | ToolResultBlockParam
        ]
    ):
        """Convert the raw result to content blocks.

        Returns:
            The content blocks representing the raw result.
        """
        if self.serialize:
            return self.serialized
        return self.result


@dataclass
class ToolResult:
    """Represents the result of using an Anthropic Tool.

    The result can include the content blocks and the interpreted return value.
    """

    use_id: str
    name: str
    raw_result: RawToolResult | None
    interpret_return_as_response: bool = False
    response_role: Literal["user", "assistant"] = "user"

    @property
    def content(self) -> str | None:
        """Get the content of the Tool Result.

        Returns:
            The content of the Tool Result, or None if there is no raw result.
        """
        return self.raw_result.serialized if self.raw_result else None

    @property
    def blocks(
        self,
    ) -> (
        str
        | Iterable[
            ToolsBetaContentBlock
            | TextBlockParam
            | ImageBlockParam
            | ToolUseBlockParam
            | ToolResultBlockParam
        ]
        | None
    ):
        """Get the content blocks of the Tool Result. Only meaningful for tools that
        have interpret_return_as_response set to True. An example use case is a tool
        that returns image content blocks.

        Returns:
            The content blocks of the Tool Result, or None if there is no raw result.
        """
        return None if self.raw_result is None else self.raw_result.as_content

    @property
    def result(self) -> Any | None:
        """Get the result of the underlying function call.

        Returns:
            The raw result of the function call
        """
        if self.raw_result:
            return self.raw_result.result
        return None