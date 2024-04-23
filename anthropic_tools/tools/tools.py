"""A definition of a tool set that can be used by Anthropic Claude."""
from __future__ import annotations
from dataclasses import dataclass
import json
from typing import (
    Any,
    Iterable,
    Literal,
    Protocol,
    TYPE_CHECKING,
    TypeGuard,
    runtime_checkable,
)

from anthropic.types import ImageBlockParam, TextBlockParam
from anthropic.types.beta.tools import (
    ToolResultBlockParam,
    ToolUseBlockParam,
    ToolsBetaContentBlock,
)
from anthropic.types.image_block_param import Source

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
class TextToolOutput:
    """The text output of a tool."""

    content: str
    is_error: bool = False
    type: Literal["text"] = "text"


@dataclass
class ImageToolOutput:
    """The image output of a tool."""

    source: Source
    type: Literal["image"] = "image"


ToolOutput = TextToolOutput | ImageToolOutput


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
    raw_result: RawToolResult
    interpret_return_as_response: bool = False
    response_role: Literal["user", "assistant"] = "user"

    @property
    def content(self) -> str:
        """Get the content of the Tool Result.

        Returns:
            The content of the Tool Result, or None if there is no raw result.
        """
        return self.raw_result.serialized

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
        """Get the content blocks of the Tool Result. Only meaningful for tools
        that have interpret_return_as_response set to True. An example use case
        is a tool that returns image content blocks.

        Returns:
            The content blocks of the Tool Result,
                or None if there is no raw result.
        """
        result = self.raw_result.as_content
        if self._is_tool_output(result):
            blocks = [
                ToolResultBlockParam(
                    type="tool_result",
                    tool_use_id=self.use_id,
                    content=[{"type": "text", "text": block.content}],
                    is_error=block.is_error,
                )
                if block.type == "text"
                else ImageBlockParam(type="image", source=block.source)
                for block in result
            ]
            if not any(block["type"] == "tool_result" for block in blocks):
                blocks.insert(
                    0,
                    ToolResultBlockParam(
                        type="tool_result",
                        tool_use_id=self.use_id,
                    ),
                )
            if len([block for block in blocks if block["type"] == "tool_result"]) > 1:
                # Replace the first result block with all concatenated results:
                first_text_block = next(
                    block for block in blocks if block["type"] == "tool_result"
                )
                first_text_block["content"] = sum(
                    [
                        list(block.get("content", []))
                        for block in blocks
                        if block["type"] == "tool_result"
                    ],
                    [],
                )
                first_text_block["is_error"] = any(
                    block["is_error"]
                    for block in blocks
                    if block["type"] == "tool_result"
                )
                # Delete all but the first one now:
                new_blocks = []
                first_done = False
                for block in blocks:
                    if block["type"] == "tool_result":
                        if first_done:
                            continue
                        else:
                            first_done = True
                    new_blocks.append(first_text_block)
                return new_blocks
            return blocks
        return result

    @property
    def result(self) -> Any | None:
        """Get the result of the underlying function call.

        Returns:
            The raw result of the function call
        """
        if self.raw_result:
            return self.raw_result.result
        return None

    def _is_tool_output(self, result: Any) -> TypeGuard[list[ToolOutput]]:
        """Check if the result is a list of ToolOutput objects.

        Args:
            result: The result to check.

        Returns:
            True if the result is a list of ToolOutput objects,
                False otherwise.
        """
        return isinstance(result, list) and all(
            isinstance(item, (TextToolOutput, ImageToolOutput)) for item in result
        )
