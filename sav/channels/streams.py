from __future__ import annotations
from inspect import getgeneratorstate, GEN_CLOSED
from itertools import chain, islice
from typing import (Any, AsyncGenerator, Awaitable, Iterable, Iterator, Optional,
                    Sequence, TypeVar)

from .abc import AbstractChannel
from .futures import Channel

_ONCE = object()
_S = TypeVar('_S', bound='StreamChannel')
_T = TypeVar('_T')


class StreamChannel(AbstractChannel[_T, None]):
    """Combining asynchronous and synchronous iteration.

    This class provides additional reading and writing methods that
    allow sending multiple items, or even synchronous unsized iterators,
    through the channel without passing control back to the event loop
    for every single item.
    """

    def __init__(self):
        self._chan = chan = Channel()
        self._send = chan.asend
        self._fetcher = fet = self._fetch()
        self._itemizer = (item async for items in fet for item in items)

    async def _fetch(self) -> AsyncGenerator[Iterator[_T], None]:
        async for items in self._chan:
            guard = (_ for _ in ())
            items = chain(items, guard)
            while getgeneratorstate(guard) != GEN_CLOSED:
                yield items

    def read_once(self) -> Awaitable[Iterator[_T]]:
        return self._fetcher.__anext__()

    async def read_items(self, n: int = -1) -> Sequence[_T]:
        buf = []
        extend = buf.extend

        if n == -1:
            async for items in self._fetcher:
                extend(items)

        elif n:
            missing = n
            async for items in self._fetcher:
                extend(islice(items, missing))
                missing = n - len(buf)
                if not missing:
                    break

        return buf

    async def wait(self) -> None:
        await self._chan.wait()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()

    async def asend(self, *values: Optional[_T]) -> Any:
        if self._fetcher.ag_await is None:
            return await self._itemizer.__anext__()
        await self._send(values)

    async def write_items(self, items: Iterable[_T]) -> None:
        await self._send(items)

    async def aclose(self) -> None:
        await self._chan.aclose()
