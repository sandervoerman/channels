from __future__ import annotations
from abc import abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncIterator, Generic, TypeVar

_T_co = TypeVar('_T_co', covariant=True)
_U_co = TypeVar('_U_co', covariant=True)


class AbstractChannel(Generic[_T_co, _U_co]):
    """Channel base class."""

    @abstractmethod
    def client(self) -> _T_co:
        raise NotImplementedError

    @abstractmethod
    async def start_server(self) -> _U_co:
        raise NotImplementedError

    @asynccontextmanager
    async def server(self) -> AsyncIterator[_U_co]:
        ser = await self.start_server()
        yield ser
        await ser.aclose()
