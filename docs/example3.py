import asyncio
from typing import AsyncIterator
from sav import channels

receiver, sender = channels.create()


async def produce() -> None:
    async with channels.open(sender):
        send_item = sender.asend
        await send_item("Item 1")
        await send_item("Item 2")
        await send_item("Item 3")
        await send_item("Item 4")


async def transform() -> AsyncIterator[str]:
    t = None
    async for item in receiver:
        if t is None:
            t = ['Combining:', item]
        else:
            t.append(item)
            s = ' '.join(t)
            yield s
            t = None


async def consume() -> None:
    async for s in transform():
        print(s)


async def main() -> None:
    await asyncio.gather(produce(), consume())


asyncio.run(main())

