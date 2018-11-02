from __future__ import annotations
from asyncio import create_task, run
from typing import AsyncIterable
from sav.channels import Channel


async def test_consumer(items: AsyncIterable):
    async for item in test_transformer(items):
        print("Consuming:", item)


async def test_transformer(items: AsyncIterable):
    t = None
    async for item in items:
        try:
            t.append(item)
        except AttributeError:
            t = ['Combining:', item]
        else:
            s = ' '.join(t)
            yield s
            t = None


async def test_producer(channel: Channel):
    async with channel as g:
        await g.asend("Item 1")
        await g.asend("Item 2")
        await g.asend("Item 3")
        await g.asend("Item 4")


async def main():
    channel = Channel()
    x = create_task(test_consumer(channel))
    y = create_task(test_producer(channel))
    await x
    await y

run(main())
