from __future__ import annotations
from contextlib import suppress, asynccontextmanager
from functools import wraps
from typing import (TypeVar, Tuple, AsyncGenerator, TYPE_CHECKING,
                    AsyncContextManager, Callable, Awaitable, AsyncIterator)
from asyncio import Future, CancelledError, get_running_loop

__all__ = ['AsyncItemizer', 'AsyncSend', 'itemizer', 'channel']

T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
T_contra = TypeVar('T_contra', contravariant=True)

# We define these public names to allow contravariant subtyping
AsyncSend = Callable[[T_contra], Awaitable[None]]
AsyncItemizer = AsyncContextManager[AsyncSend[T_contra]]

if TYPE_CHECKING:
    _Request = Future['_Response[T_co]']
    _Response = Tuple[T_co, Future[_Request[T_co]]]


def itemizer(f: Callable) -> Callable:
    @wraps(f)
    @asynccontextmanager
    async def wrapper(*args, **kwargs):
        sender = f(*args, **kwargs)
        await sender.asend(None)
        yield sender.asend
        await sender.aclose()
    return wrapper


def channel() -> Tuple[AsyncIterator[T], AsyncItemizer[T]]:
    """Rendezvous channel between two coroutines."""
    create = get_running_loop().create_future

    async def iterate(req: _Request[T]) -> AsyncGenerator[T, None]:
        with suppress(CancelledError):
            while True:
                item, confirm = await req
                yield item
                req = create()
                confirm.set_result(req)

    @itemizer
    async def itemize(req: _Request[T]) -> AsyncGenerator[None, T]:
        try:
            while True:
                confirm = create()
                req.set_result(((yield), confirm))
                req = await confirm
        except GeneratorExit:
            req.cancel()

    init_req = create()
    return iterate(init_req), itemize(init_req)
