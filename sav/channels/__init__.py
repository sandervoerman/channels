"""Point-to-point object streams between coroutines."""
from __future__ import annotations
from typing import Any, AsyncContextManager, AsyncIterator, Awaitable, Generic, Optional, TypeVar, Union
from asyncio import get_running_loop

from .streams import Reader, Writer

_S = TypeVar('_S', bound='Channel')
_T = TypeVar('_T')
_V = TypeVar('_V')


class _Created:
    def __init__(self, channel):
        self.channel = channel

    def set_result(self, value):
        if value is not None:
            raise TypeError
        self.channel._create = get_running_loop().create_future


class _Closed:
    def set_result(self, value):
        raise StopAsyncIteration


class Channel(Generic[_T, _V]):
    _create: Any = None

    def __init__(self):
        self._fut: Any = _Created(self)

    def __aiter__(self: _S) -> _S:
        return self

    client = server = __aiter__

    def __anext__(self) -> Awaitable[_T]:
        return self.asend(None)

    def asend(self, value: Optional[Union[_T, _V]]) -> Awaitable:
        self._fut.set_result(value)
        self._fut = self._create()
        return self._fut

    def _status(self) -> type:
        return type(self._fut)

    async def wait(self) -> None:
        if self._status() is _Created:
            await self.asend(None)

    async def __aenter__(self: _S) -> _S:
        await self.wait()
        return self

    async def aclose(self) -> None:
        status = self._status()
        if status is not _Closed:
            if status is not _Created:
                self._fut.set_exception(StopAsyncIteration)
            self._fut = _Closed()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()


class StreamChannel(Generic[_T]):
    def __init__(self):
        self._chan = Channel()

    def __aiter__(self) -> AsyncIterator[_T]:
        return self.client().__aiter__()

    def client(self) -> Reader[_T]:
        return Reader(self._chan.client())

    def server(self) -> AsyncContextManager[Writer[_T]]:
        return self

    async def __aenter__(self) -> Writer[_T]:
        await self._chan.wait()
        return Writer(self._chan)

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self._chan.aclose()
