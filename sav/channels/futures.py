from __future__ import annotations
from asyncio import get_running_loop


class _Created:
    def __init__(self, channel):
        self.channel = channel

    def set_result(self, value):
        if value is not None:
            raise TypeError
        self.channel._create = get_running_loop().create_future


class _Closed:
    def set_result(self, value):
        raise StopAsyncIteration


class SimpleChannel:
    _create = None

    def __init__(self):
        self._fut = _Created(self)

    def __aiter__(self):
        return self

    def _status(self):
        return type(self._fut)

    async def wait(self):
        if self._status() is _Created:
            await self.asend(None)

    def __anext__(self):
        return self.asend(None)

    def asend(self, value):
        self._fut.set_result(value)
        self._fut = self._create()
        return self._fut

    async def aclose(self):
        status = self._status()
        if status is not _Closed:
            if status is not _Created:
                self._fut.set_exception(StopAsyncIteration)
            self._fut = _Closed()


