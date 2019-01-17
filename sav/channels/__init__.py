"""Point-to-point object streams between coroutines."""
import asyncio

__all__ = ['Channel']


def _fgen():
    """Yield futures and set sent values as their results."""
    create_future = asyncio.get_running_loop().create_future
    aitem = create_future()
    try:
        while True:
            aitem.set_result((yield aitem))
            aitem = create_future()
    finally:
        aitem.cancel()


async def _agen(gen, aitem):
    """Asynchronous generator adapter."""
    send = gen.send
    try:
        while True:
            aitem = send((yield await aitem))
    except asyncio.CancelledError:
        pass
    except GeneratorExit:
        gen.close()


class Channel:
    """Rendezvous channel between two coroutines."""

    def __init__(self, cli_call=_agen, ser_call=_agen):
        gen = _fgen()
        self.server = ser_call(gen, gen.send(None))
        self.client = cli_call(gen, gen.send(None))

    def __aiter__(self):
        return self.client

    async def __aenter__(self):
        await self.server.asend(None)
        return self.server

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.server.aclose()
