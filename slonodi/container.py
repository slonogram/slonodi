from __future__ import annotations
from typing import TypeAlias, Optional, Dict, Type, Any, TypeVar, Callable

from slonogram.dispatching.context import Context

T = TypeVar("T")
MapFn: TypeAlias = Callable[[Context[Any, Any]], T]
ValueOrMapFn: TypeAlias = T | MapFn[T]


class Container:
    __slots__ = "parent", "_deps"

    def __init__(self, parent: Optional[Container] = None) -> None:
        self.parent = parent
        self._deps: Dict[Type, Any] = {}

    def dependency(self, ty: Type[T], dep: ValueOrMapFn[T]) -> Container:
        new = Container(self.parent)
        self._deps = {**self._deps, ty: dep}
        return new

    def __setitem__(self, item: Type[T], value: ValueOrMapFn[T]) -> None:
        self._deps[item] = value

    def __getitem__(self, item: Type[T]) -> ValueOrMapFn[T]:
        try:
            return self._deps[item]
        except KeyError as e:
            parent = self.parent
            if parent is not None:
                return parent[item]
            raise KeyError(
                f"failed to find type {item.__name__!r} in the container"
            ) from e

    def with_parent(self, parent: Container) -> Container:
        new = Container(parent)
        new._deps = self._deps
        return new


__all__ = ["Container"]
