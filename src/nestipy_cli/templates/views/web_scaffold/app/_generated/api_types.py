from __future__ import annotations

from typing import Any, Protocol, TypeVar, Generic, Callable

T = TypeVar("T")

class JsPromise(Protocol, Generic[T]):
    def then(
        self,
        on_fulfilled: Callable[[T], Any] | None = ...,
        on_rejected: Callable[[Any], Any] | None = ...,
    ) -> "JsPromise[Any]": ...

class ApiClient(Protocol):
    pass
