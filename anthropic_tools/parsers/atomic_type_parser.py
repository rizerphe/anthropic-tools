"""Parser for atomic json types"""
from __future__ import annotations
from typing import Any, Protocol, TYPE_CHECKING, Type, TypeVar

from ..exceptions import BrokenSchemaError
from .parser import ArgSchemaParser

if TYPE_CHECKING:
    from ..json_type import JsonType
    from typing_extensions import TypeGuard

T = TypeVar("T")


class AtomicParser(ArgSchemaParser[T], Protocol[T]):
    """Parser for atomic json values"""

    _type: Type[T]

    @property
    def schema_type_name(self) -> str:
        """Name of the type in the json schema"""
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def argument_schema(self) -> dict[str, JsonType]:
        return {
            "type": self.schema_type_name,
        }

    @classmethod
    def can_parse(cls, argtype: Any) -> TypeGuard[Type[T]]:
        return argtype is cls._type

    def parse_value(self, value: JsonType) -> T:
        if not isinstance(value, self._type):
            raise BrokenSchemaError(value, self.argument_schema)
        return value
