from __future__ import annotations
import asyncio
import itertools
from typing import AsyncIterator, AsyncContextManager, AsyncGenerator, Callable
from unittest import TestCase
from sav.channels import Reader, Writer, AbstractChannel, Channel, StreamChannel


async def simplex_consume(items: AsyncIterator[str]):
    results = []
    async for item in simplex_transform(items):
        results.append(item)
    return results


async def simplex_transform(items: AsyncIterator[str]):
    t = None
    async for item in items:
        if t is None:
            t = ['Combining:', item]
        else:
            t.append(item)
            s = ' '.join(t)
            yield s
            t = None


async def simplex_produce(cm: AsyncContextManager[AsyncGenerator[None, str]]):
    async with cm as sender:
        send_item = sender.asend
        await send_item("Item 1")
        await send_item("Item 2")
        await send_item("Item 3")
        await send_item("Item 4")


async def simplex_main(factory: Callable):
    c = factory()
    _, consumed = await asyncio.gather(simplex_produce(c.server()),
                                       simplex_consume(c.client()))
    return consumed


duplex_results = []


async def duplex_letters(cm: AsyncContextManager[AsyncGenerator[int, str]]):
    async with cm as server:
        duplex_results.append(await server.asend("A"))
        duplex_results.append(await server.asend("B"))


async def duplex_numbers(client: AsyncGenerator[str, int]):
    try:
        duplex_results.append(await client.__anext__())
        for i in itertools.count():
            duplex_results.append(await client.asend(i))
    except StopAsyncIteration:
        pass


async def duplex_main():
    channel = Channel()
    client, cm = channel.client(), channel.server()
    await asyncio.gather(duplex_letters(cm), duplex_numbers(client))
    return duplex_results


class TestChannel(TestCase):

    def test_simplex(self):
        self.assertEqual(asyncio.run(simplex_main(Channel)),
                         ['Combining: Item 1 Item 2',
                          'Combining: Item 3 Item 4'])

    def test_duplex(self):
        self.assertEqual(asyncio.run(duplex_main()),
                         ['A', 0, 'B', 1])


async def stream_read_all(reader: Reader):
    return await reader.read_items()


async def stream_write(cm: AsyncContextManager[Writer]):
    async with cm as writer:
        writer.write_items(range(10))


class TestStreamChannel(TestCase):

    def test_simplex(self):
        self.assertEqual(asyncio.run(simplex_main(StreamChannel)),
                         ['Combining: Item 1 Item 2',
                          'Combining: Item 3 Item 4'])
