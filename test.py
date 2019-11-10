from __future__ import annotations
import asyncio
from io import StringIO
import itertools
from typing import (AsyncContextManager, AsyncGenerator, AsyncIterator, List,
                    TypeVar, Union)
import unittest
from sav import channels

_T = TypeVar('_T')

Receiver = Union[AsyncIterator[_T], channels.Reader[_T]]
Sender = Union[AsyncGenerator[None, _T], channels.Writer[_T]]

def _open(sender: Sender) -> AsyncContextManager:
    if isinstance(sender, channels.Writer):
        return sender
    return channels.open(sender)


class TestReadme(unittest.TestCase):
    def test_example(self):
        result = StringIO()

        # Use channels.create() to create new channels.
        a_receiver, a_sender = channels.create()
        b_receiver, b_sender = channels.create()

        async def send_messages():
            """Send messages into multiple channels."""

            # Use channels.open() to start the generators that you want to send
            # values into. Each generator will wait until their channel is
            # iterated over from the other end.
            async with channels.open(a_sender), channels.open(b_sender):
                # The content of the async with block is similar to the body of
                # an asynchronous generator function. However, instead of using
                # yield statements to generate the values for a single iterator,
                # we can send different values to different iterators.
                await a_sender.asend('Hello Arnold.')
                await b_sender.asend('Hello Bernard.')
                await a_sender.asend('Goodbye Arnold.')
                await b_sender.asend('Goodbye Bernard.')

                # When control flows out of this code block, each context
                # manager will close the generator it started. Closing a
                # generator at one end of a channel causes the generator at the
                # other end to raise StopAsyncIteration.

        async def show_messages(name, receiver):
            """Show messages from a single channel."""
            async for message in receiver:
                print(f'Message for {name}: {message}', file=result)

        async def main():
            """Run both channels concurrently."""
            await asyncio.gather(
                send_messages(),
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
        async def produce(sender: Sender[str]) -> None:
            async with _open(sender):
                send_item = sender.asend
                await send_item("Item 1")
                await send_item("Item 2")
                await send_item("Item 3")
                await send_item("Item 4")

        async def transform(items: Receiver[str]) -> AsyncIterator[str]:
            t = None
            async for item in items:
                if t is None:
                    t = ['Combining:', item]
                else:
                    t.append(item)
                    s = ' '.join(t)
                    yield s
                    t = None

        async def consume(items: Receiver[str]) -> List[str]:
            return [s async for s in transform(items)]

        for f in channels.create, channels.stream:
            with self.subTest(f=f):
                x, y = f()
                _, result = await asyncio.gather(produce(y), consume(x))
                self.assertEqual(result, ['Combining: Item 1 Item 2',
                                          'Combining: Item 3 Item 4'])

    async def test_stream(self):
        async def write(channel: channels.Writer[int]) -> None:
            async with channel:
                await channel.write_items(range(10))

        async def read_all(channel: channels.Reader[int]):
            return await channel.read_items()

        r, w = channels.stream()
        result, _ = await asyncio.gather(read_all(r), write(w))
        self.assertEqual(result, list(range(10)))

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
