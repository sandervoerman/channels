"""Point-to-point object streams between coroutines."""
from __future__ import annotations
from inspect import getgeneratorstate, GEN_CREATED
from typing import TypeVar, AsyncGenerator

from .abc import AbstractChannel, ChannelClosed
from .streams import Reader, Writer

_T = TypeVar('_T')
_U = TypeVar('_U')


class Channel(AbstractChannel[AsyncGenerator[_T, _U], AsyncGenerator[_U, _T]]):
    def client(self) -> AsyncGenerator[_T, _U]:
        return self._generate(False)

    async def _generate(self, is_server) -> AsyncGenerator:
        msg = None
        send = self._alt.send
        try:
            if is_server:
                if getgeneratorstate(self._alt) == GEN_CREATED:
                    await next(self._alt)
                msg = yield

            while True:
                msg = yield await send(msg)
        except ChannelClosed:
            pass
        except GeneratorExit:
            self._alt.close()

    async def start_server(self) -> AsyncGenerator[_U, _T]:
        ser = self._generate(True)
        await ser.asend(None)
        return ser


class StreamChannel(AbstractChannel[Reader[_T], Writer[_T]]):
    def client(self) -> Reader[_T]:
        return Reader(self._alt)

    async def start_server(self) -> Writer[_T]:
        if getgeneratorstate(self._alt) == GEN_CREATED:
            await next(self._alt)
        return Writer(self._alt)
