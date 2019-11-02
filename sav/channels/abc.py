from __future__ import annotations
from abc import abstractmethod
from contextlib import asynccontextmanager
from typing import (AsyncContextManager, Awaitable, Generic, Optional, TypeVar,
                    Union)

_C = TypeVar('_C', bound='AbstractChannel')
_T = TypeVar('_T')
_V = TypeVar('_V')


class AbstractChannel(Generic[_T, _V]):
    """The core channel API."""

    def __init__(self):
        self._managers = [None, None]

    def __aiter__(self: _C) -> _C:
        return self

    def __anext__(self) -> Awaitable[_T]:
        return self.asend(None)

    def __aenter__(self: _C) -> Awaitable[_C]:
        return self.open(wait=True).__aenter__()

    def __aexit__(self, *args) -> Awaitable[Optional[bool]]:
        return self._managers[True].__aexit__(*args)

    @asynccontextmanager
    async def _open(self, wait):
        try:
            if wait:
                await self.wait()
            yield self
        except StopAsyncIteration:
            pass
        finally:
            self._managers[wait] = None
            await self.aclose()

    def open(self, *, wait: bool) -> AsyncContextManager:
        """Open the channel from one of the two ends.

        :param wait: Specifies whether the context manager should wait
            for the other end to request the first item, before
            returning control to the caller.

            Note that the caller that sets this to `True` gets to send
            the first item. The context manager will wait until the
            other end has requested the first item. Conversely, the
            caller that sets this to `False` will immediately enter the
            context, but is responsible for starting the channel by
            sending `None` into it.
        """
        managers = self._managers
        if managers[wait] is None:
            managers[wait] = m = self._open(wait)
        else:
            raise RuntimeError(f'Already open for {wait=}.')
        return m

    @abstractmethod
    def asend(self, value: Optional[Union[_T, _V]]) -> Awaitable:
        raise NotImplementedError

    @abstractmethod
    def wait(self) -> Awaitable:
        raise NotImplementedError

    @abstractmethod
    def aclose(self) -> Awaitable:
        raise NotImplementedError

