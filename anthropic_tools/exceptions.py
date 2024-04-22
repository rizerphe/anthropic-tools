"""The exceptions associated with Anthropic Tools."""

from __future__ import annotations
from typing import Any


class AnthropicToolsError(Exception):
    """Base class for exceptions raised by Anthropic Tools."""


class ToolNotFoundError(AnthropicToolsError):
    """The requested tool is not found.

    Attributes:
        tool_name (str): The name of the tool that was not found.
    """

    def __init__(self, tool_name: str) -> None:
        """Initialize the ToolNotFoundError.

        Args:
            tool_name (str): The name of the tool that was not found.
        """
        super().__init__(f"Tool {tool_name} not found.")
        self.tool_name = tool_name


class CannotParseTypeError(AnthropicToolsError):
    """The type of an argument cannot be parsed.

    Attributes:
        argtype (Any): The type that cannot be parsed.
    """

    def __init__(self, argtype: Any) -> None:
        """Initialize the CannotParseTypeError.

        Args:
            argtype (Any): The type that cannot be parsed.
        """
        super().__init__(f"Cannot parse type {argtype}")
        self.argtype = argtype


class NonSerializableOutputError(AnthropicToolsError):
    """The tool output is not JSON-serializable.

    Attributes:
        result (Any): The result that is not JSON-serializable.
    """

    def __init__(self, result: Any) -> None:
        """Initialize the NonSerializableOutputError.

        Args:
            result (Any): The result that is not JSON-serializable.
        """
        super().__init__(
            f"The result {result} is not JSON-serializable. "
            "Set serialize=False to use str() instead."
        )
        self.result = result


class BrokenSchemaError(AnthropicToolsError):
    """The response from Anthropic does not match the schema.

    Attributes:
        response (Any): The response that does not match the schema.
        schema (Any): The schema that the response should match.
    """

    def __init__(self, response: Any, schema: Any) -> None:
        """Initialize the BrokenSchemaError.

        Args:
            response (Any): The response that does not match the schema.
            schema (Any): The schema that the response should match.
        """
        super().__init__(
            "Anthropic returned a response that did not match the schema: "
            f"{response!r} does not match {schema}"
        )
        self.response = response
        self.schema = schema
