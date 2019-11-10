from __future__ import annotations
from inspect import isgenerator
from itertools import chain, islice
from typing import (TypeVar, Awaitable, Iterator, Sequence, Iterable,
                    Generator, AsyncIterator, Generic, AsyncGenerator)

__ALL__ = ['Reader', 'Writer']

_T = TypeVar('_T')
_T_co = TypeVar('_T_co', covariant=True)
_T_contra = TypeVar('_T_contra', contravariant=True)


def _guard(*items: _T) -> Generator[_T, None, None]:
    yield from items


class Reader(Generic[_T_co]):
    """Generic stream reader protocol.

    Generic API similar to the standard input streams, except that
    instead of bytes or strings, iterables of custom object types are
    read from the stream.

    This protocol defines additional reading methods that allow
    receiving multiple items, or even synchronous unsized iterators,
    through the channel.
    """

    def __init__(self, iterables: AsyncGenerator[Iterable, None],
                 keep_alive: bool) -> None:
        self._iterables = iterables
        self._close = not keep_alive
        self._fetcher = self._fetch()

    async def _fetch(self) -> AsyncGenerator[Iterator[_T], None]:
        try:
            async for iterable in self._iterables:
                if isgenerator(iterable):
                    guard = iterable
                else:
                    iterable = chain(iterable, guard := _guard())

                while guard.gi_frame:
                    yield iterable

        except GeneratorExit:
            await self._iterables.aclose()

    async def __aenter__(self) -> Reader[_T_co]:
        return self

    async def __aiter__(self) -> AsyncIterator[_T_co]:
        async for items in self._fetcher:
            for item in items:
                yield item

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._close:
            await self._fetcher.aclose()
        return exc_type is StopAsyncIteration

    def read_once(self) -> Awaitable[Iterator[_T_co]]:
        return self._fetcher.__anext__()

    async def read_items(self, n: int = -1) -> Sequence[_T_co]:
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


class Writer(Generic[_T_contra]):
    """Generic stream writer protocol.

    Generic API similar to the standard output streams, except that
    instead of bytes or strings, iterables of custom object types are
    written to the stream.

    This protocol defines additional writing methods that allow sending
    multiple items, or even synchronous unsized iterators, through the
    channel without passing control back to the event loop for every
    single item.
    """

    def __init__(self, iterables: AsyncGenerator[None, Iterable],
                 keep_alive: bool) -> None:
        self._iterables = iterables
        self._clear = not keep_alive
        self._asend_iterable = self._iterables.asend

    async def __aenter__(self) -> None:
        await self._iterables.__anext__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self._iterables.aclose()
        return self._clear and exc_type is StopAsyncIteration

    def asend(self, value: _T_contra) -> Awaitable[None]:
        return self._asend_iterable(_guard(value))

    def write_items(self, items: Iterable[_T_contra]) -> Awaitable[None]:
        return self._asend_iterable(items)
