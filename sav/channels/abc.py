from __future__ import annotations
from abc import abstractmethod
from asyncio import Future, get_running_loop
from contextlib import asynccontextmanager
from inspect import getgeneratorstate, GEN_SUSPENDED
from itertools import repeat, starmap, tee
from typing import Any, AsyncIterator, Generator, Generic, Iterator, Tuple, TypeVar

_T_co = TypeVar('_T_co', covariant=True)
_U_co = TypeVar('_U_co', covariant=True)


Connection = Generator[Tuple[Iterator[Future], Iterator[Future]], None, None]


class ChannelClosed(Exception):
    pass


class FutureEnd:
    setters = None
    waiters = None

    def __init__(self, con: Connection) -> None:
        self.con = con

    def open(self) -> None:
        self.waiters, self.setters = next(self.con)

    async def start_server(self) -> Any:
        self.open()
        return await next(self.waiters)

    def close(self) -> None:
        if getgeneratorstate(self.con) == GEN_SUSPENDED:
            self.con.close()
            next(self.setters).set_exception(ChannelClosed)

    def zipped(self) -> Iterator[Tuple[Future, Future]]:
        return zip(self.setters, self.waiters)


def _create_connection() -> Connection:
    s = starmap(get_running_loop().create_future, repeat(()))
    a, b = zip(tee(s), tee(s))
    yield a
    yield reversed(b)


class AbstractChannel(Generic[_T_co, _U_co]):
    """Channel base class."""

    def __init__(self):
        self._con = _create_connection()

    def _connect(self) -> FutureEnd:
        return FutureEnd(self._con)

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
