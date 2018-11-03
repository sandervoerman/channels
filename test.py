from __future__ import annotations
from asyncio import create_task, run
from typing import AsyncIterable
from sav.channels import channel, AsyncItemizer


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


async def test_producer(items: AsyncItemizer):
    async with items as send_item:
        await send_item("Item 1")
        await send_item("Item 2")
        await send_item("Item 3")
        await send_item("Item 4")


async def main():
    iterator, itemizer = channel()
    x = create_task(test_consumer(iterator))
    y = create_task(test_producer(itemizer))
    await x
    await y

run(main())
