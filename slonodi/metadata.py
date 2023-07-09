from typing import TypeVar, Generic
from slonogram.handling.scratches.scratch import Scratch

T = TypeVar("T")
R = TypeVar("R")


class FromPad(Generic[T, R]):
    __slots__ = ("scratch",)

    def __init__(self, scratch: Scratch[T, R]) -> None:
        self.scratch = scratch


class Dependency:
    def __init__(self) -> None:
        pass


__all__ = ["FromPad", "Dependency"]
