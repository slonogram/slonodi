from __future__ import annotations

from .container import Container, MapFn
from .metadata import Dependency, FromPad
from inspect import signature, isfunction, Signature

from typing import (
    TypeVar,
    TypeAlias,
    Callable,
    Any,
    Awaitable,
    get_origin,
    Annotated,
    Dict,
    get_args,
)
from functools import partial

from slonogram.bot import Bot
from slonogram.handling.scratches.scratch import Scratch
from slonogram.dispatching.context import Context

D = TypeVar("D")
T = TypeVar("T")
R = TypeVar("R")

InjectableFn: TypeAlias = Callable[..., Any]
InjectedFn: TypeAlias = Callable[[Context[D, T]], Awaitable[None]]


# identity
def _provide_ctx(ctx: Context[D, T]) -> Context[D, T]:
    return ctx


def _provide_scratch(
    r_stub: R, scratch: Scratch[T, R], ctx: Context[D, T]
) -> R:
    _ = r_stub
    return ctx.pad.get(scratch)


def _provide_bot(ctx: Context[D, T]) -> Bot:
    return ctx.inter.bot


class _CallHandler:
    __slots__ = (
        "kwds",
        "deferred",
        "func",
        "__treat_as_context__",
        "__name__",
    )

    def __init__(
        self,
        kwds: Dict[str, Any],
        deferred: Dict[str, MapFn[Any]],
        func: InjectableFn,
    ) -> None:
        self.kwds = kwds
        self.deferred = deferred
        self.func = func

        self.__name__ = getattr(func, "__name__", repr(func))
        self.__treat_as_context__ = True

    def __call__(self, context: Context[D, T]) -> Awaitable[None]:
        return self.func(
            **self.kwds,
            **{k: f(context) for k, f in self.deferred.items()},
        )


class Injector:
    def __init__(self, container: Container) -> None:
        self.container = container

    def __call__(self, fn: InjectableFn) -> InjectedFn[D, T]:
        sig = signature(fn)

        eager: Dict[str, Any] = {}
        deferred: Dict[str, MapFn[Any]] = {}
        assumed_model_annotation = Signature.empty

        for name, parameter in sig.parameters.items():
            if parameter.kind == parameter.POSITIONAL_ONLY:
                raise TypeError(
                    "functions with positional-only arguments"
                    " are not supported"
                )
            elif parameter.annotation is Signature.empty:
                raise TypeError(
                    "parameters without annotations are not supported"
                )
            hint = parameter.annotation
            origin = get_origin(hint)

            if origin is Context:
                deferred[name] = _provide_ctx
            elif parameter.annotation == Bot:
                deferred[name] = _provide_bot
            elif origin is Annotated:
                meta = hint.__metadata__
                if len(meta) != 1:
                    raise TypeError(
                        f"unexpected type metadata size"
                        f": {len(meta)} (expected 1)"
                    )

                (meta,) = meta  # type: ignore
                if isinstance(meta, Dependency) or meta is Dependency:
                    ty, *_ = get_args(hint)
                    dep = self.container[ty]
                    if isfunction(dep):
                        deferred[name] = dep
                    else:
                        eager[name] = dep
                elif isinstance(meta, FromPad):
                    deferred[name] = partial(
                        _provide_scratch, None, meta.scratch
                    )
                else:
                    raise TypeError("passed unknown metadata type")
            elif (
                origin is None
                and assumed_model_annotation is Signature.empty
            ):
                assumed_model_annotation = hint
            else:
                raise TypeError(
                    f"Don't know how to handle type {hint}"
                    f" (assuming that model type "
                    f"is the {assumed_model_annotation})"
                )

        return _CallHandler(eager, deferred, fn)
