from __future__ import annotations
from abc import abstractmethod
from typing import Any, Awaitable, Generic, Optional, TypeVar, Union


_C = TypeVar('_C', bound='AbstractChannel')
_T = TypeVar('_T')
_V = TypeVar('_V')


class AbstractChannel(Generic[_T, _V]):
    """The core channel API."""
    def __aiter__(self: _C) -> _C:
        return self

    @abstractmethod
    def asend(self, value: Optional[Union[_T, _V]]) -> Awaitable:
        raise NotImplementedError

    def __anext__(self) -> Awaitable[_T]:
        return self.asend(None)

    @abstractmethod
    def wait(self) -> Awaitable:
        raise NotImplementedError

    async def __aenter__(self: _C) -> _C:
        await self.wait()
        return self

    @abstractmethod
    def aclose(self) -> Awaitable:
        raise NotImplementedError

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()
