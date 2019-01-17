from types import TracebackType
from typing import (Any, AsyncGenerator, Awaitable, Callable, Generator,
                    Generic, Optional, Type, TypeVar)

_X = TypeVar('_X')
_Y = TypeVar('_Y')
_Gen = Generator[Awaitable, Any, None]
_Call = Callable[[_Gen, Awaitable], AsyncGenerator[_X, _Y]]

def _fgen() -> _Gen: ...
async def _agen(gen: _Gen, aitem: Awaitable) -> AsyncGenerator: ...

class Channel(Generic[_X, _Y]):
    client: AsyncGenerator[_X, _Y]
    server: AsyncGenerator[_Y, _X]

    def __init__(self, cli_call: _Call[_X, _Y] = ..., ser_call: _Call[_Y, _X] = ...): ...
    def __aiter__(self) -> AsyncGenerator[_X, _Y]: ...
    def __aenter__(self) -> Awaitable[AsyncGenerator[_Y, _X]]: ...
    def __aexit__(self, exc_type: Optional[Type[BaseException]],
                  exc_value: Optional[BaseException],
                  traceback: Optional[TracebackType]) -> Awaitable[Optional[bool]]: ...
