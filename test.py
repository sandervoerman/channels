from __future__ import annotations
import asyncio
import itertools
from sav.channels import Channel


async def test_consumer(simplex: Channel[str, None]):
    async for item in test_transformer(simplex):
        print("Consuming:", item)


async def test_transformer(simplex: Channel[str, None]):
    t = None
    async for item in simplex:
        if t is None:
            t = ['Combining:', item]
        else:
            t.append(item)
            s = ' '.join(t)
            yield s
            t = None


async def test_producer(simplex: Channel[str, None]):
    async with simplex as sender:
        send_item = sender.asend
        await send_item("Item 1")
        await send_item("Item 2")
        await send_item("Item 3")
        await send_item("Item 4")


async def letters(duplex: Channel[str, int]):
    async with duplex:
        print(await duplex.server.asend("A"))
        print(await duplex.server.asend("B"))


async def numbers(duplex: Channel[str, int]):
    try:
        print(await duplex.client.__anext__())
        for i in itertools.count():
            print(await duplex.client.asend(i))
    except StopAsyncIteration:
        pass


async def main():
    simplex: Channel[str, None] = Channel()
    duplex: Channel[str, int] = Channel()

    await asyncio.gather(test_producer(simplex), test_consumer(simplex))
    await asyncio.gather(letters(duplex), numbers(duplex))

asyncio.run(main())
