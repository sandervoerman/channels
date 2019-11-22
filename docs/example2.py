import asyncio
import itertools
from typing import AsyncGenerator
from sav import channels


async def numbers(c: AsyncGenerator[str, int]) -> None:
    async with channels.open(c, start=False):
        print(await c.asend(None))
        for i in itertools.count():
            print(await c.asend(i))


async def letters(c: AsyncGenerator[int, str]) -> None:
    async with channels.open(c):
        print(await c.asend("A"))
        print(await c.asend("B"))


async def main() -> None:
    c_left, c_right = channels.create()
    await asyncio.gather(numbers(c_left), letters(c_right))


asyncio.run(main())
