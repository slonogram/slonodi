from typing import (
    Dict,
    Type,
    Any,
    Optional,
    Self,
    TypeVar,
    Callable,
    TypeAlias,
    NoReturn,
)

T = TypeVar("T")
ConstF: TypeAlias = Callable[[], T]
_sentinel = object()


def const(value: T) -> Callable[[], T]:
    def f(*args, **kwargs) -> T:
        _ = args
        _ = kwargs
        return value

    return f


def throw(
    e: Exception, from_: Optional[Exception] = None
) -> Callable[[], NoReturn]:
    def inner_throw() -> NoReturn:
        if from_ is not None:
            raise e from from_
        raise e

    return inner_throw


class Container:
    def __init__(self) -> None:
        self._instances: Dict[Type, Any] = {}
        self._child: Optional[Self] = None

    def get(
        self,
        ty: Type[T],
        default: ConstF[T] = throw(
            IndexError("failed to resolve dependency")
        ),
        insert_default: bool = False,
    ) -> T:
        result = self._instances.get(ty, _sentinel)
        if result is _sentinel:
            result = default()
            if insert_default:
                self._instances[ty] = result
        return result

    @property
    def child(self) -> Optional[Self]:
        return self._child


__all__ = ["Container", "const", "throw"]
