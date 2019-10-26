"""Point-to-point object streams between coroutines."""
from __future__ import annotations
from typing import TypeVar, AsyncGenerator

from .abc import AbstractChannel
from .futures import SimpleChannel
from .streams import Reader, Writer

_T = TypeVar('_T')
_V = TypeVar('_V')


class Channel(AbstractChannel[_T, AsyncGenerator[_T, _V], AsyncGenerator[_V, _T]]):
    def __init__(self):
        self._simple = SimpleChannel()

    def client(self) -> AsyncGenerator[_T, _V]:
        return self._simple

    async def start_server(self) -> AsyncGenerator[_V, _T]:
        await self._simple.wait()
        return self._simple


class StreamChannel(AbstractChannel[_T, Reader[_T], Writer[_T]]):
    def __init__(self):
        self._chan = Channel()

    def client(self) -> Reader[_T]:
        return Reader(self._chan.client())

    async def start_server(self) -> Writer[_T]:
        return Writer(await self._chan.start_server())
