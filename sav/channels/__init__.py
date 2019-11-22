"""Channels between coroutines.

A simple Python_ implementation of the channel_ synchronization
construct for `async/await`_ applications.

Channels are used for synchronization in the CSP_ concurrency model.
They are natively supported by languages that implement this model, such
as occam_ and Go_. Python has `asynchronous generators`_, which are
similar to channels except that they require yielding instead of calling
from one of the two endpoints. While this makes no difference in many
cases, some problems are easier to solve if a data stream can be
accessed from both ends by calling instead of yielding.

The :mod:`!sav.channels` module implements channels as pairs of
asynchronous generators. When an object is sent into one generator, it
will be yielded by the other generator, and vice-versa.

.. _Python: https://www.python.org/
.. _channel: https://en.wikipedia.org/wiki/Channel_(programming)
.. _async/await: https://www.python.org/dev/peps/pep-0492/
.. _CSP: http://www.usingcsp.com/
.. _occam: http://www.wotug.org/occam/
.. _Go: https://tour.golang.org/concurrency/2
.. _asynchronous generators: https://www.python.org/dev/peps/pep-0525/

"""
from __future__ import annotations
from asyncio import get_running_loop
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Tuple, TypeVar

__all__ = ['create', 'open']

_AG = TypeVar('_AG', bound=AsyncGenerator)


def create() -> Tuple[AsyncGenerator, AsyncGenerator]:
    """Create a new channel.

    :returns: A pair of asynchronous generators. When an object is sent
              into one of the generators, it is yielded by the other,
              and vice-versa.
    """

    fut = None

    async def generate(wait: bool) -> AsyncGenerator:
        nonlocal fut
        try:
            if fut is not None:
                fut.set_result((yield) if wait else None)

            f = get_running_loop().create_future
            while True:
                item = await (fut := f())
                fut.set_result((yield item))

        except EOFError:
            pass

        except GeneratorExit:
            if fut is not None:
                fut.set_exception(EOFError)

    return generate(False), generate(True)


@asynccontextmanager
async def open(ag: _AG, *, start: bool = True, clear: bool = True,
               close: bool = True) -> AsyncGenerator[_AG, None]:
    """Use a context manager to start and close a generator.

    :param ag: The async generator.
    :param start: Whether the generator should be started.
    :param clear: Whether StopAsyncIteration should be cleared.
    :param close: Whether the generator should be closed.
    :returns: The async context manager.
    """

    try:
        if start:
            await ag.asend(None)
        yield ag

    except StopAsyncIteration:
        if not clear:
            raise

    finally:
        if close:
            await ag.aclose()
