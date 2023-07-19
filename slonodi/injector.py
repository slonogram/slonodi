from __future__ import annotations

from functools import partial
from inspect import signature
from typing import (
    Callable,
    List,
    Any,
    Dict,
    TypeVar,
    Generic,
    Optional,
    Sequence,
    Tuple,
)
from abc import ABC, abstractmethod

from .container import Container
from .specifiers import Specifier, DeferredEvaluation


T = TypeVar("T")
C = TypeVar("C")


class Provider(Generic[C], ABC):
    @abstractmethod
    def provide_container(self, ctx: C) -> Container:
        raise NotImplementedError

    @abstractmethod
    def provide_ctx(self, data: Any) -> C:
        raise NotImplementedError


class Injector(Generic[C]):
    def __init__(
        self,
        provider: Provider[C],
        default_specifiers: Sequence[Specifier] = [],
        map_injected: Optional[
            Callable[[InjectedFn[Any, C]], None]
        ] = None,
    ) -> None:
        self.default_specifiers = default_specifiers
        self.provider = provider
        self.map_injected = map_injected

    def inject(
        self, *specifiers: Specifier
    ) -> Callable[[Callable[..., T]], InjectedFn[T, C]]:
        def inner(fn: Callable[..., T]) -> InjectedFn[T, C]:
            return InjectedFn[T, C](
                (*self.default_specifiers, *specifiers), self.provider, fn
            )

        return inner


class InjectedFn(Generic[T, C]):
    def __init__(
        self,
        specifiers: Tuple[Specifier, ...],
        provider: Provider[C],
        fn: Callable[..., T],
    ) -> None:
        self._applied_fn: Optional[Callable[..., T]] = None
        self._deferred: List[DeferredEvaluation] = []
        self._specifiers = specifiers
        self._provider = provider
        self._fn = fn

    def _initialize(self, context: C) -> None:
        out: Dict[str, Any] = {}
        params = signature(self._fn).parameters
        container = self._provider.provide_container(context)

        for specifier in self._specifiers:
            res = specifier.write_dependencies(params, container)
            if callable(res):
                self._deferred.append(res)
            else:
                out.update(res)
        self._applied_fn = partial(self._fn, **out)

    def __call__(self, context: C) -> T:
        applied_fn = self._applied_fn
        if applied_fn is None:
            self._initialize(context)
            applied_fn = self._applied_fn

        deferred: Dict[str, Any] = {}
        for item in self._deferred:
            deferred.update(item(context))

        return applied_fn(**deferred)  # type: ignore


__all__ = ["InjectedFn", "Injector", "Provider"]
