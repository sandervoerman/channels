from __future__ import annotations
from asyncio import Future, get_running_loop
from contextlib import suppress
from typing import Any, Awaitable, Callable, Optional, TypeVar, Union

from .abc import AbstractChannel

_C = TypeVar('_C', bound='Channel')
_T = TypeVar('_T')
_V = TypeVar('_V')


class _Created:
    @staticmethod
    def set_result(value: Any) -> None:
        if value is not None:
            raise TypeError


class _Closed:
    @staticmethod
    def set_result(value: Any) -> None:
        raise StopAsyncIteration


class Channel(AbstractChannel[_T, _V]):
    """The default implementation of the channel API.

    This class can be used for unidirectional or bidirectional
    communication. In the unidirectional case, the receiving coroutine
    can use an ``async for`` block while the transmitting coroutine uses
    an ``async with`` block::

        import asyncio
        from sav.channels import Channel
        from foo import Foo

        async def produce(c: Channel[Foo, None]) -> None:
            # Open channel for transmission
            async with c:
                await c.asend(Foo("One"))
                await produce_two(c)
                await c.asend(Foo("Three"))

        async def produce_two(c: Channel[Foo, None]) -> None:
            # No async with statement, the channel is already open
            await c.asend(Foo("Two"))

        async def consume(c: Channel[Foo, None]) -> None:
            async for foo in c:
                print(foo)

        async def main() -> None:
            c = Channel()
            await asyncio.gather(consume(c), produce(c))

        asyncio.run(main())

    The channel's context manager will wait until the receiving
    coroutine starts iterating, at which point the transmitting
    coroutine resumes inside the async with block. When the end of the
    async with block is reached, the context manager will schedule
    `StopAsyncIteration` to be raised at the receiving end.

    The following example demonstrates how data flows through the
    channel in the case of bidirectional communication::

        import asyncio
        import itertools
        from sav.channels import Channel

        async def letters(c: Channel[str, int]) -> None:
            async with c.open(wait=True):    # wait
                print(await c.asend("A"))    # send and receive
                print(await c.asend("B"))    # send and receive

        async def numbers(c: Channel[str, int]) -> None:
            async with c.open(wait=False):   # don't wait
                print(await c.asend(None))   # receive only
                for i in itertools.count():
                    print(await c.asend(i))  # send and receive

        async def main() -> None:
            c = Channel()
            await asyncio.gather(letters(c), numbers(c))

        asyncio.run(main())

    This will produce the result::

        A
        0
        B
        1

    """

    _fut: Any = _Created

    def __init__(self):
        super().__init__()
        self._create_future: Callable[[], Future] = self._create_first_future

    def _create_first_future(self) -> Future:
        self._create_future = f = get_running_loop().create_future
        return f()

    def asend(self, value: Optional[Union[_T, _V]]) -> Awaitable:
        self._fut.set_result(value)
        self._fut = self._create_future()
        return self._fut

    async def wait(self) -> None:
        if self._fut is _Created:
            await self.asend(None)

    async def aclose(self) -> None:
        with suppress(AttributeError):
            self._fut.set_exception(StopAsyncIteration)
        self._fut = _Closed
