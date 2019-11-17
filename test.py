import asyncio
import io
import itertools
import unittest
from typing import AsyncIterator, List
import mypy.api
from sav import channels


class TestTyping(unittest.TestCase):
    def test_mypy(self) -> None:
        args = ['--namespace-packages', '-c', 'import sav.channels']
        out, err, code = mypy.api.run(args)
        self.assertEqual(code, 0, msg=out+err)


class TestSimplex(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.__receiver, self.__sender = channels.create()

    async def __produce(self) -> None:
        async with channels.open(self.__sender):
            send_item = self.__sender.asend
            await send_item("Item 1")
            await send_item("Item 2")
            await send_item("Item 3")
            await send_item("Item 4")

    async def __transform(self) -> AsyncIterator[str]:
        t = None
        async for item in self.__receiver:
            if t is None:
                t = ['Combining:', item]
            else:
                t.append(item)
                s = ' '.join(t)
                yield s
                t = None

    async def __consume(self) -> List[str]:
        return [s async for s in self.__transform()]

    async def test_pipe(self) -> None:
        _, result = await asyncio.gather(self.__produce(), self.__consume())
        self.assertEqual(result, ['Combining: Item 1 Item 2',
                                  'Combining: Item 3 Item 4'])

class TestDuplex(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.__left, self.__right = channels.create()
        self.__result = []

    async def __letters(self) -> None:
        async with channels.open(self.__left) as g:
            self.__result.append(await g.asend("A"))
            self.__result.append(await g.asend("B"))

    async def __numbers(self) -> None:
        async with channels.open(self.__right) as g:
            self.__result.append(await g.__anext__())
            for i in itertools.count():
                self.__result.append(await g.asend(i))

    async def test_duplex(self) -> None:
        await asyncio.gather(self.__letters(), self.__numbers())
        self.assertEqual(self.__result, ['A', 0, 'B', 1])


class TestReadme(unittest.TestCase):
    def test_example(self) -> None:
        result = io.StringIO()
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
