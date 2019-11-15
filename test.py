from __future__ import annotations
import asyncio
from io import StringIO
import itertools
from typing import AsyncGenerator, AsyncIterator, List, Union
import unittest
from sav import channels


class TestReadme(unittest.TestCase):
    def test_example(self):
        result = StringIO()
        a_receiver, a_sender = channels.create()
        b_receiver, b_sender = channels.create()

        async def send_messages():
            """Send messages into multiple channels."""
            async with channels.open(a_sender), channels.open(b_sender):
                await a_sender.asend('Hello Arnold.')
                await b_sender.asend('Hello Bernard.')
                await a_sender.asend('Goodbye Arnold.')
                await b_sender.asend('Goodbye Bernard.')

        async def show_messages(name, receiver):
            """Show messages from a single channel."""
            async for message in receiver:
                print(f'Message for {name}: {message}', file=result)

        async def main():
            """Run both channels concurrently."""
            await asyncio.gather(send_messages(),
                                 show_messages('Arnold', a_receiver),
                                 show_messages('Bernard', b_receiver))

        asyncio.run(main())
        self.assertEqual(
            result.getvalue(),
            'Message for Arnold: Hello Arnold.\n'
            'Message for Bernard: Hello Bernard.\n'
            'Message for Arnold: Goodbye Arnold.\n'
            'Message for Bernard: Goodbye Bernard.\n'
        )


class TestChannels(unittest.IsolatedAsyncioTestCase):

    async def test_pipe(self):
        async def produce(sender: AsyncGenerator[None, str]) -> None:
            async with channels.open(sender):
                send_item = sender.asend
                await send_item("Item 1")
                await send_item("Item 2")
                await send_item("Item 3")
                await send_item("Item 4")

        async def transform(items: AsyncIterator[str]) -> AsyncIterator[str]:
            t = None
            async for item in items:
                if t is None:
                    t = ['Combining:', item]
                else:
                    t.append(item)
                    s = ' '.join(t)
                    yield s
                    t = None

        async def consume(items: AsyncIterator[str]) -> List[str]:
            return [s async for s in transform(items)]

        x, y = channels.create()
        _, result = await asyncio.gather(produce(y), consume(x))
        self.assertEqual(result, ['Combining: Item 1 Item 2',
                                  'Combining: Item 3 Item 4'])

    async def test_duplex(self):
        async def letters(g: AsyncGenerator[int, str],
                          result: List[Union[str, int]]):
            async with channels.open(g):
                result.append(await g.asend("A"))
                result.append(await g.asend("B"))

        async def numbers(g: AsyncGenerator[str, int],
                          result: List[Union[str, int]]):
            async with channels.open(g):
                result.append(await g.__anext__())
                for i in itertools.count():
                    result.append(await g.asend(i))

        c, r = channels.create(), []
        await asyncio.gather(letters(c[0], r), numbers(c[1], r))
        self.assertEqual(r, ['A', 0, 'B', 1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
