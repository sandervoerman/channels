import asyncio
from sav import channels

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
        print(f'Message for {name}: {message}')


async def main():
    """Run both channels concurrently."""
    await asyncio.gather(send_messages(),
                         show_messages('Arnold', a_receiver),
                         show_messages('Bernard', b_receiver))


asyncio.run(main())
