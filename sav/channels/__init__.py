"""Point-to-point object streams between coroutines."""
from __future__ import annotations
from typing import TypeVar, AsyncGenerator

from .abc import AbstractChannel
from .futures import ChannelClosed, create_connection, FutureEnd
from .streams import Reader, Writer

_T = TypeVar('_T')
_U = TypeVar('_U')


class Channel(AbstractChannel[AsyncGenerator[_T, _U], AsyncGenerator[_U, _T]]):
    def __init__(self):
        self._con = create_connection()

    def client(self) -> AsyncGenerator[_T, _U]:
        return self._generate(False)

    async def _generate(self, is_server) -> AsyncGenerator:
        msg = None
        end = FutureEnd(self._con)
        try:
            if is_server:
                await end.start_server()
                msg = yield

            else:
                end.open()

            for setter, waiter in end.zipped():
                setter.set_result(msg)
                msg = yield await waiter

        except ChannelClosed:
            pass

        finally:
            end.close()

    async def start_server(self) -> AsyncGenerator[_U, _T]:
        ser = self._generate(True)
        await ser.asend(None)
        return ser


class StreamChannel(AbstractChannel[Reader[_T], Writer[_T]]):
    def __init__(self):
        self._chan = Channel()

    def client(self) -> Reader[_T]:
        return Reader(self._chan.client())

    async def start_server(self) -> Writer[_T]:
        return Writer(await self._chan.start_server())
