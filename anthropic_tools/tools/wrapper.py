"""A wrapper that turns ordinary functions into Anthropic Tools."""
from __future__ import annotations
from dataclasses import dataclass
import inspect
from typing import Any, Callable, OrderedDict, TYPE_CHECKING, Type

from anthropic.types.beta.tools import ToolParam
from docstring_parser import Docstring, parse

from ..exceptions import BrokenSchemaError, CannotParseTypeError
from ..parsers import ArgSchemaParser, defargparsers

if TYPE_CHECKING:
    from ..json_type import JsonType


@dataclass
class WrapperConfig:
    """Configuration options for the ToolWrapper."""

    parsers: list[Type[ArgSchemaParser]] | None = None
    save_return: bool = True
    serialize: bool = True
    interpret_as_response: bool = False


class ToolWrapper:
    """A wrapper that turns ordinary functions into Anthropic Tools."""

    def __init__(
        self,
        func: Callable[..., Any],
        config: WrapperConfig | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Initialize the ToolWrapper.

        Args:
            func: The function to be wrapped.
            config: Configuration options for the wrapper.
            name: The name of the tool.
            description: The description of the tool.
        """
        self.func = func
        self.config = config or WrapperConfig()
        self._name = name
        self._description = description

    @property
    def parsers(self) -> list[Type[ArgSchemaParser]]:
        """Get the list of argument schema parsers.

        Returns:
            The list of argument schema parsers.
        """
        return self.config.parsers or defargparsers

    @property
    def save_return(self) -> bool:
        """Get the flag indicating whether to save the return value.

        Returns:
            The flag indicating whether to save the return value.
        """
        return self.config.save_return

    @property
    def serialize(self) -> bool:
        """Get the flag indicating whether to serialize the arguments.

        Returns:
            The flag indicating whether to serialize the arguments.
        """
        return self.config.serialize

    @property
    def interpret_as_response(self) -> bool:
        """Get the flag indicating whether to interpret the result as a response.

        Returns:
            The flag indicating whether to interpret the result as a response.
        """
        return self.config.interpret_as_response

    @property
    def argument_parsers(self) -> OrderedDict[str, ArgSchemaParser]:
        """Get the ordered dictionary of argument parsers.

        Returns:
            The ordered dictionary of argument parsers.
        """
        return OrderedDict(
            (
                (name, self.parse_argument(argument))
                for name, argument in inspect.signature(self.func).parameters.items()
            )
        )

    @property
    def required_arguments(self) -> list[str]:
        """Get the list of required arguments.

        Returns:
            The list of required arguments.
        """
        return [
            name
            for name, argument in inspect.signature(self.func).parameters.items()
            if argument.default is argument.empty
        ]

    @property
    def arguments_schema(self) -> JsonType:
        """Get the schema for the arguments.

        Returns:
            The schema for the arguments.
        """
        return {
            name: {
                **parser.argument_schema,
                **(
                    {"description": self.arg_docs.get(name)}
                    if name in self.arg_docs
                    else {}
                ),
            }
            for name, parser in self.argument_parsers.items()
        }

    @property
    def parsed_docs(self) -> Docstring:
        """Get the parsed docstring.

        Returns:
            The parsed docstring.
        """
        return parse(self.func.__doc__ or "")

    @property
    def arg_docs(self) -> dict[str, str]:
        """Get the dictionary of argument descriptions.

        Returns:
            The dictionary of argument descriptions.
        """
        return {
            param.arg_name: param.description
            for param in self.parsed_docs.params
            if param.description
        }

    @property
    def name(self) -> str:
        """Get the name of the tool.

        Returns:
            The name of the tool.
        """
        return self._name or self.func.__name__

    @property
    def schema(self) -> ToolParam:
        """Get the schema for the tool.

        Returns:
            The schema for the tool.
        """
        schema: ToolParam = {
            "name": self.name,
            "input_schema": {
                "type": "object",
                "properties": self.arguments_schema,
                "required": self.required_arguments,  # type: ignore
            },
        }
        description = self.parsed_docs.short_description or self._description
        if description:
            schema["description"] = description
        return schema

    def parse_argument(self, argument: inspect.Parameter) -> ArgSchemaParser:
        """Parse the argument using the appropriate argument schema parser.

        Args:
            argument: The argument to be parsed.

        Returns:
            The argument schema parser.

        Raises:
            CannotParseTypeError: If the argument type is not supported.
        """
        for parser in self.parsers:
            if parser.can_parse(argument.annotation):
                return parser(argument.annotation, self.parsers)
        raise CannotParseTypeError(argument.annotation)

    def parse_arguments(self, arguments: dict[str, JsonType]) -> OrderedDict[str, Any]:
        """Parse the arguments using the argument parsers.

        Args:
            arguments: The arguments to be parsed.

        Returns:
            The ordered dictionary of parsed arguments.

        Raises:
            BrokenSchemaError: If the arguments do not match the schema.
        """
        argument_parsers = self.argument_parsers
        if not all(name in arguments for name in self.required_arguments):
            raise BrokenSchemaError(arguments, self.arguments_schema)
        try:
            return OrderedDict(
                (
                    (name, argument_parsers[name].parse_value(value))
                    for name, value in arguments.items()
                )
            )
        except KeyError as err:
            raise BrokenSchemaError(arguments, self.arguments_schema) from err

    def __call__(self, arguments: dict[str, JsonType]) -> Any:
        """Call the wrapped function with the parsed arguments.

        Args:
            arguments: The arguments to be passed to the function.

        Returns:
            The result of calling the function.
        """
        return self.func(**self.parse_arguments(arguments))
