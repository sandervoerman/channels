from __future__ import annotations
from contextlib import suppress
from typing import TypeVar, Tuple, AsyncGenerator, TYPE_CHECKING, Generic
from asyncio import Future, CancelledError, get_running_loop

__all__ = ['Channel']

T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
T_contra = TypeVar('T_contra', contravariant=True)


if TYPE_CHECKING:
    _Request = Future['_Response[T_co]']
    _Response = Tuple[T_co, Future[_Request[T_co]]]


async def _create_receiver(req: _Request[T]) -> AsyncGenerator[T, None]:
    create = get_running_loop().create_future
    with suppress(CancelledError):
        while True:
            item, confirm = await req
            yield item
            req = create()
            confirm.set_result(req)


async def _create_transmitter(req: _Request[T]) -> AsyncGenerator[None, T]:
    create = get_running_loop().create_future
    try:
        while True:
            confirm = create()
            req.set_result(((yield), confirm))
            req = await confirm
    except GeneratorExit:
        req.cancel()


class Channel(Generic[T]):
    """Rendezvous channel between two coroutines."""

    def __init__(self):
        req: _Request[T] = get_running_loop().create_future()
        self.receiver = _create_receiver(req)
        self.transmitter = _create_transmitter(req)

    async def __aenter__(self) -> AsyncGenerator[None, T]:
        await self.transmitter.asend(None)
        return self.transmitter

    def __aiter__(self) -> AsyncGenerator[T, None]:
        return self.receiver

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.transmitter.aclose()
