"""Parser for null types"""
from __future__ import annotations
from typing import Any, TYPE_CHECKING, Type

from ..exceptions import BrokenSchemaError
from .parser import ArgSchemaParser

if TYPE_CHECKING:
    from ..json_type import JsonType
    from typing_extensions import TypeGuard


class NoneParser(ArgSchemaParser[None]):
    """Parser for null types"""

    @property
    def argument_schema(self) -> dict[str, JsonType]:
        return {"type": "null"}

    @classmethod
    def can_parse(cls, argtype: Any) -> TypeGuard[Type[None]]:
        return argtype in [None, type(None)]

    def parse_value(self, value: JsonType) -> None:
        if value is not None:
            raise BrokenSchemaError(value, self.argument_schema)
