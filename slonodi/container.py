from typing import Optional, Dict, Type, Any, TypeVar

T = TypeVar("T")


class Container:
    __slots__ = "_raw", "parent"

    def __init__(self, parent: Optional["Container"] = None) -> None:
        self._raw: Dict[Type, Any] = {}
        self.parent = parent

    def __getitem__(self, ty: Type[T]) -> T:
        try:
            return self._raw[ty]
        except KeyError as e:
            if self.parent is not None:
                return self.parent[ty]
            raise e from e

    def __setitem__(self, dep_ty: Type[T], dep: T) -> None:
        self._raw[dep_ty] = dep
