from types import TracebackType
from typing import (Any, AsyncGenerator, Awaitable, Callable, Generator,
                    Generic, Optional, Type, TypeVar)

_S = TypeVar('_S')
_T = TypeVar('_T')
_Ca = Callable[[Generator[Awaitable, Any, None], Awaitable], AsyncGenerator[_S, _T]]

class Channel(Generic[_S, _T]):
    client: AsyncGenerator[_S, _T]
    server: AsyncGenerator[_T, _S]

    def __init__(self, cli_call: _Ca[_S, _T] = ..., ser_call: _Ca[_T, _S] = ...): ...
    def __aiter__(self) -> AsyncGenerator[_S, _T]: ...
    def __aenter__(self) -> Awaitable[AsyncGenerator[_T, _S]]: ...
    def __aexit__(self, exc_type: Optional[Type[BaseException]],
                  exc_value: Optional[BaseException],
                  traceback: Optional[TracebackType]) -> Awaitable[Optional[bool]]: ...
