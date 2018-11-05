from __future__ import annotations
from asyncio import create_task, run
from typing import AsyncIterable, AsyncIterator
from sav.channels import Channel, AsyncItemizer


async def test_consumer(items: AsyncIterable[str]) -> None:
    async for item in test_transformer(items):
        print("Consuming:", item)


async def test_transformer(items: AsyncIterable[str]) -> AsyncIterator[str]:
    t = None
    async for item in items:
        if t is None:
            t = ['Combining:', item]
        else:
            t.append(item)
            s = ' '.join(t)
            yield s
            t = None


async def test_producer(items: AsyncItemizer[str]) -> None:
    async with items as send_item:
        await send_item("Item 1")
        await send_item("Item 2")
        await send_item("Item 3")
        await send_item("Item 4")


async def main() -> None:
    c: Channel[str] = Channel()
    x = create_task(test_consumer(c.receiver))
    y = create_task(test_producer(c.sender))
    await x
    await y

run(main())
