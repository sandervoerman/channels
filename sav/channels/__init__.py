"""Point-to-point object streams between coroutines."""
from __future__ import annotations
from contextlib import suppress
from typing import TypeVar, AsyncGenerator

from .abc import AbstractChannel, ChannelClosed
from .streams import Reader, Writer

_T = TypeVar('_T')
_U = TypeVar('_U')


class Channel(AbstractChannel[AsyncGenerator[_T, _U], AsyncGenerator[_U, _T]]):
    async def client(self) -> AsyncGenerator[_T, _U]:
        req = None
        send = self._alt.send
        with suppress(ChannelClosed):
            while True:
                req = yield await send(req)

    async def _server(self) -> AsyncGenerator[_U, _T]:
        req = None
        send = self._alt.send
        try:
            while True:
                req = await send((yield req))
        finally:
            self._alt.close()

    async def start_server(self, req) -> AsyncGenerator[_U, _T]:
        ser = self._server()
        await ser.asend(None)
        return ser


class StreamChannel(AbstractChannel[Reader[_T], Writer[_T]]):
    def client(self) -> Reader[_T]:
        return Reader(self._alt)

    async def start_server(self, req) -> Writer[_T]:
        return Writer(self._alt, req)
