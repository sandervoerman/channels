from __future__ import annotations
from asyncio import gather
from itertools import count
from typing import AsyncIterator, List, TypeVar, Union
from unittest import IsolatedAsyncioTestCase, main
from sav.channels import Channel, StreamChannel

_T = TypeVar('_T')

SimplexChannel = Union[Channel[_T, None], StreamChannel[_T]]


class TestChannels(IsolatedAsyncioTestCase):

    async def test_pipe(self):
        async def produce(channel: SimplexChannel[str]) -> None:
            async with channel:
                send_item = channel.asend
                await send_item("Item 1")
                await send_item("Item 2")
                await send_item("Item 3")
                await send_item("Item 4")

        async def transform(channel: SimplexChannel[str]) -> AsyncIterator[str]:
            t = None
            async for item in channel:
                if t is None:
                    t = ['Combining:', item]
                else:
                    t.append(item)
                    s = ' '.join(t)
                    yield s
                    t = None

        async def consume(channel: SimplexChannel[str]) -> List[str]:
            return [s async for s in transform(channel)]

        for cls in Channel, StreamChannel:
            with self.subTest(cls=cls):
                c: SimplexChannel[str] = cls()
                _, result = await gather(produce(c), consume(c))
                self.assertEqual(result, ['Combining: Item 1 Item 2',
                                          'Combining: Item 3 Item 4'])

    async def test_stream(self):
        async def write(channel: StreamChannel[int]) -> None:
            async with channel:
                await channel.write_items(range(10))

        async def read_all(channel: StreamChannel[int]):
            return await channel.read_items()

        c = StreamChannel()
        result, _ = await gather(read_all(c), write(c))
        self.assertEqual(result, list(range(10)))

    async def test_duplex(self):
        async def letters(channel: Channel[str, int], result: List[Union[str, int]]):
            async with channel.open(wait=True):
                result.append(await channel.asend("A"))
                result.append(await channel.asend("B"))

        async def numbers(channel: Channel[str, int], result: List[Union[str, int]]):
            async with channel.open(wait=False):
                result.append(await channel.__anext__())
                for i in count():
                    result.append(await channel.asend(i))

        c, r = Channel(), []
        await gather(letters(c, r), numbers(c, r))
        self.assertEqual(r, ['A', 0, 'B', 1])


if __name__ == '__main__':
    main(verbosity=2)
