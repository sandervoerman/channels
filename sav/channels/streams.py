from __future__ import annotations
from inspect import getgeneratorstate, GEN_CLOSED
from itertools import chain, islice
from typing import Any, AsyncIterator,  Generic, Iterable, Iterator, Sequence, TypeVar

_ONCE = object()
_T = TypeVar('_T')
_T_co = TypeVar('_T_co', covariant=True)
_T_contra = TypeVar('_T_contra', contravariant=True)


async def _fetcher(end: AsyncIterator[Iterable[_T]]) -> AsyncIterator[Iterator[_T]]:
    async for items in end:
        guard = (_ for _ in ())
        items = chain(items, guard)
        while getgeneratorstate(guard) != GEN_CLOSED:
            yield items


async def _itemizer(fet: AsyncIterator[Iterable[_T]]) -> AsyncIterator[_T]:
    async for items in fet:
        for x in items:
            yield x


class Reader(Generic[_T_co]):
    def __init__(self, end: Any):
        self._fetcher = fet = _fetcher(end)
        self._itemizer = _itemizer(fet)

    def __aiter__(self) -> AsyncIterator[_T_co]:
        return self._itemizer

    async def read_once(self) -> Iterator[_T_co]:
        return await self._fetcher.__anext__()

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
    def __init__(self, end: Any):
        self._end = end
        self._send = end.asend

    async def asend(self, *args: _T_contra) -> None:
        await self._send(args)

    async def write_items(self, items: Iterable[_T_contra]) -> None:
        await self._send(items)

    async def aclose(self) -> None:
        await self._end.aclose()
