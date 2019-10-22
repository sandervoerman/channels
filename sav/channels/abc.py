from abc import abstractmethod
from asyncio import get_running_loop
from contextlib import asynccontextmanager
from itertools import starmap, repeat
from typing import TypeVar, Generator, Awaitable, Any, Generic, AsyncIterator

_T_co = TypeVar('_T_co', covariant=True)
_U_co = TypeVar('_U_co', covariant=True)
_SERVER = object()


class ChannelClosed(Exception):
    pass


def _alternator() -> Generator[Awaitable, Any, None]:
    fut = None
    try:
        for fut in starmap(get_running_loop().create_future, repeat(())):
            fut.set_result((yield fut))
    finally:
        if fut is not None:
            fut.set_exception(ChannelClosed)


class AbstractChannel(Generic[_T_co, _U_co]):
    """Channel base class.

    When a value is sent into the alternator, it is set as the result of
    the previously yielded future, and a new future is returned to the
    caller. By awaiting the future, the caller prevents itself from getting
    its own value back, and will instead receive the value sent by the next
    caller. Hence, the direction in which values are sent and received
    is alternated upon every iteration.

    The alternator finalizes by setting `ChannelClosed` on the most
    recently yielded future. When one coroutine closes the alternator, the
    other coroutine is scheduled to be called soon, and
    control is passed back to the former coroutine.
    """

    def __init__(self):
        self._alt = _alternator()

    @abstractmethod
    def client(self) -> _T_co:
        raise NotImplementedError

    @abstractmethod
    async def start_server(self) -> _U_co:
        raise NotImplementedError

    @asynccontextmanager
    async def server(self) -> AsyncIterator[_U_co]:
        ser = await self.start_server()
        yield ser
        await ser.aclose()
