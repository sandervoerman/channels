from __future__ import annotations
from asyncio import Future, get_running_loop
from contextlib import suppress
from typing import Any, Awaitable, Callable, Generic, Optional, TypeVar, Union

from .abc import AbstractChannel

_C = TypeVar('_C', bound='Channel')
_T = TypeVar('_T')
_V = TypeVar('_V')


class _Created:
    @staticmethod
    def set_result(value: Any) -> None:
        if value is not None:
            raise TypeError


class _Closed:
    @staticmethod
    def set_result(value: Any) -> None:
        raise StopAsyncIteration


class Channel(AbstractChannel[_T, _V]):
    _fut: Any = _Created

    def __init__(self):
        self._create_future: Callable[[], Future] = self._create_first_future

    def _create_first_future(self) -> Future:
        self._create_future = f = get_running_loop().create_future
        return f()

    def asend(self, value: Optional[Union[_T, _V]]) -> Awaitable:
        self._fut.set_result(value)
        self._fut = self._create_future()
        return self._fut

    async def wait(self) -> None:
        if self._fut is _Created:
            await self.asend(None)

    async def aclose(self) -> None:
        with suppress(AttributeError):
            self._fut.set_exception(StopAsyncIteration)
        self._fut = _Closed
