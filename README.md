# Channels between coroutines in Python
This package provides channels between coroutines with async/await 
syntax.

## What is a channel?
A channel is a pair of asynchronous generators, such that when an object
is sent into one generator, it will be yielded by the other generator.

## Example

```python
import asyncio
from sav import channels

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
        print(f'Message for {name}: {message}')    

async def main():
    """Run both channels concurrently."""
    await asyncio.gather(
        send_messages(),
        show_messages('Arnold', a_receiver),
        show_messages('Bernard', b_receiver))

asyncio.run(main())
```

## Features

 * Bidirectional sending and receiving.
 * Easy to refactor from, or into, asynchronous generators.
 * Can be used as an adaptor for asynchronous generator pipelines to invert 
   the directions in which data is being sent into, and yielded from, the
   pipeline.
 * Delegate item transmission to other coroutines by simply passing them the
   channel object.
 * Feed different values to different iterator objects from within a single
   coroutine or asynchronous generator function.  
 * Read or write multiple items at once to avoid cycling through the event loop 
   for every single item.
 * Delegate item transmission to synchronous generators and read from them in
   the receiving coroutine.
 
See the documentation in the source code for further details and examples.
