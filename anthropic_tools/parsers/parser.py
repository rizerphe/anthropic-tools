"""A protocol for a parser for a specific argument type."""
from __future__ import annotations
from typing import Any, Protocol, TYPE_CHECKING, Type, TypeVar

from ..exceptions import CannotParseTypeError

if TYPE_CHECKING:
    from ..json_type import JsonType
    from typing_extensions import TypeGuard

T = TypeVar("T")
S = TypeVar("S")


class ArgSchemaParser(Protocol[T]):
    """A protocol for a parser for a specific argument type

    Both converts the argument definition to a JSON schema and parses the argument value
    from JSON import
    """

    argtype: Type[T]
    rec_parsers: list[Type[ArgSchemaParser]]

    def __init__(
        self, argtype: Type[T], rec_parsers: list[Type[ArgSchemaParser]]
    ) -> None:
        self.argtype = argtype
        self.rec_parsers = rec_parsers

    @property
    def argument_schema(self) -> dict[str, JsonType]:
        """Parse an argument of a specific type"""
        ...  # pylint: disable=unnecessary-ellipsis

    @classmethod
    def can_parse(cls, argtype: Any) -> TypeGuard[Type[T]]:
        """Whether this parser can parse a specific arg type

        Args:
            argtype (Any): The type to check
        """
        ...  # pylint: disable=unnecessary-ellipsis

    def parse_rec(self, argtype: Type[S]) -> ArgSchemaParser[S]:
        """Parse a type recursively

        Args:
            argtype (Type[S]): The type to parse

        Returns:
            ArgSchemaParser[S]: The parser for the type

        Raises:
            CannotParseTypeError: If the type cannot be parsed
        """
        for parser in self.rec_parsers:
            if parser.can_parse(argtype):
                return parser(argtype, self.rec_parsers)
        raise CannotParseTypeError(argtype)

    def parse_value(self, value: JsonType) -> T:
        """Parse a value of a specific type

        Args:
            value (JsonType): The value to parse

        Raises:
            BrokenSchemaError: If the value does not match the schema
        """
        ...  # pylint: disable=unnecessary-ellipsis
