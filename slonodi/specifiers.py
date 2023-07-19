from typing import Protocol, Mapping, Any, Dict, Tuple, Callable, TypeAlias
from inspect import Parameter

from .container import Container


DeferredEvaluation: TypeAlias = Callable[[Any], Dict[str, str]]


class Specifier(Protocol):
    def write_dependencies(
        self,
        parameters: Mapping[str, Parameter],
        # black, please insert here the newline
        # thanks!
        container: Container,
        /,
    ) -> Dict[str, Any] | Tuple[Dict[str, Any], DeferredEvaluation]:
        ...


class RequiresSpecifier:
    __slots__ = ("names",)

    def __init__(self, names: Tuple[str, ...]) -> None:
        self.names = names

    def write_dependencies(
        self,
        parameters: Mapping[str, Parameter],
        # same here
        container: Container,
        /,
    ) -> Dict[str, Any] | DeferredEvaluation:
        out: Dict[str, Any] = {}

        for name in self.names:
            parameter = parameters[name]
            annot = parameter.annotation

            if annot is Parameter.empty:
                raise TypeError(
                    f"Type annotation for {name!r} is not specified: "
                    f"not sure about the requested dependency"
                )
            dependency = container[annot]

            out[name] = dependency

        return out


def requires(*names: str) -> RequiresSpecifier:
    return RequiresSpecifier(names)


__all__ = [
    "requires",
    "RequiresSpecifier",
    "Specifier",
    "DeferredEvaluation",
]
