"""Point-to-point object streams between coroutines"""
from __future__ import annotations
from contextlib import suppress, asynccontextmanager
from typing import (TypeVar, AsyncGenerator, Generic, AsyncContextManager,
                    Callable, Awaitable, AsyncIterator)
from asyncio import Future, get_running_loop, CancelledError

__all__ = ['AsyncItemize', 'AsyncItemizer', 'Channel']

T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
T_contra = TypeVar('T_contra', contravariant=True)

# Public types for co- and contravariant typing
AsyncItemize = Callable[[T_contra], Awaitable[None]]
AsyncItemizer = AsyncContextManager[AsyncItemize[T_contra]]


class Channel(Generic[T]):
    """Rendezvous channel between two coroutines"""

    sender: AsyncItemizer[T]
    receiver: AsyncIterator[T]

    def __init__(self):
        self._create = get_running_loop().create_future
        self._pull = self._create()
        self.sender = self._sender()
        self.receiver = self._receiver()

    @asynccontextmanager
    async def _sender(self) -> AsyncGenerator[AsyncItemize[T], None]:
        async def send(item):
            (await self._pull).set_result(item)
            self._pull = self._create()
        try:
            yield send
        finally:
            (await self._pull).cancel()

    async def _receiver(self) -> AsyncIterator[T]:
        with suppress(CancelledError):
            for push in iter(self._create, None):
                self._pull.set_result(push)
                yield await push
