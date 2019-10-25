from __future__ import annotations
from abc import abstractmethod
from typing import (Any, AsyncContextManager, AsyncIterable, AsyncIterator, Generic,
                    TypeVar)

_C_co = TypeVar('_C_co', bound=AsyncIterable, covariant=True)
_S_co = TypeVar('_S_co', covariant=True)

_T = TypeVar('_T')


class AbstractChannel(Generic[_T, _C_co, _S_co]):
    """Channel base class."""
    __server: Any = None

    @abstractmethod
    def client(self) -> _C_co:
        raise NotImplementedError

    def __aiter__(self) -> AsyncIterator[_T]:
        return self.client().__aiter__()

    @abstractmethod
    async def start_server(self) -> _S_co:
        raise NotImplementedError

    def server(self) -> AsyncContextManager[_S_co]:
        return self

    async def __aenter__(self) -> _S_co:
        self.__server = await self.start_server()
        return self.__server

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.__server.aclose()
