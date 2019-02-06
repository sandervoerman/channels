from contextlib import suppress
from itertools import islice
from typing import (TypeVar, Generic, Generator, Awaitable, Any, AsyncIterator,
                    Iterator, Sequence, Iterable)

from .abc import ChannelClosed

_ONCE = object()
_T_co = TypeVar('_T_co', covariant=True)
_T_contra = TypeVar('_T_contra', contravariant=True)


class Reader(Generic[_T_co]):
    def __init__(self, alt: Generator[Awaitable, Any, Any]):
        self._alt = alt
        self._send = alt.send

    async def __aiter__(self) -> AsyncIterator[_T_co]:
        with suppress(ChannelClosed):
            for fut in self._alt:
                yield await fut

    async def read_once(self) -> Iterator[_T_co]:
        return await self._send(_ONCE)

    async def read_items(self, n: int = -1) -> Sequence[_T_co]:
        return () if n == 0 else await self._send(n)


class Writer(Generic[_T_contra]):
    def __init__(self, alt: Generator[Awaitable, Any, Any], req: Any):
        self._alt = alt
        self._send = alt.send
        self._buf = []
        self._req = req

    async def asend(self, value: _T_contra) -> None:
        req = self._req

        if req is None:
            self._req = await self._send(value)

        elif req is _ONCE:
            self._req = await self._send(iter((value,)))

        else:
            buf = self._buf
            buf.append(value)
            if len(buf) == req:
                self._req = await self._send(buf)
                self._buf = []

    async def write_items(self, items: Iterable[_T_contra]) -> None:
        send = self._send
        items = iter(items)
        while True:
            req = self._req

            if req is _ONCE:
                self._req = await send(items)
                return

            if req == -1:
                self._buf.extend(items)
                return

            if req is None:
                try:
                    self._req = await send(next(items))
                except StopIteration:
                    return

            else:
                buf = self._buf
                buf.extend(islice(items, req - len(buf)))
                if len(buf) < req:
                    return
                self._req = await send(buf)
                self._buf = []

    async def aclose(self) -> None:
        if self._buf:
            await self._send(self._buf)
        self._alt.close()
