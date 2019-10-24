from __future__ import annotations
from asyncio import Future, get_running_loop
from inspect import getgeneratorstate, GEN_SUSPENDED
from itertools import repeat, starmap, tee
from typing import Any, Generator, Iterator, Tuple


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


def create_connection() -> Connection:
    s = starmap(get_running_loop().create_future, repeat(()))
    a, b = zip(tee(s), tee(s))
    yield a
    yield reversed(b)


