# Channels between coroutines in Python
This package provides channels between coroutines with async/await syntax.

## What is a channel?
A channel is a pair of asynchronous generators, such that when an object is 
sent into one generator, it will be yielded by the other generator.

## Example
The following script shows how channels can be used to send messages into
concurrent `async for` loops:

```python
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
```

Result:

```
Message for Arnold: Hello Arnold.
Message for Bernard: Hello Bernard.
Message for Arnold: Goodbye Arnold.
Message for Bernard: Goodbye Bernard.
```

The example demonstrates the following features:

 * `channels.create()` creates a new channel. It returns a tuple of two
   asynchronous generators.
 * `channels.open()` handles startup and cleanup of the second generator
   of each channel. It returns a context manager that starts and closes
   the generator. 
 * Each generator waits until its counterpart is started by the
   `async for` loop at the other end of the channel.
 * When control flows out of the `async with` block, the context
   managers close the reverse generators, and each reverse generator 
   schedules its counterpart at the `async for` end of the channel to 
   raise a `StopAsyncIteration` exception.


## Additional features/usage

 * All channels are bidirectional by default: you can open both ends with
   `channels.open()` and use the `asend` method of each generator to send and 
   receive objects back and forth. 
 * The `async with` block is easy to refactor from, or back into, an
   asynchronous generator function.
 * Channels can be used as adaptors for asynchronous generator pipelines,
   reversing the directions in which data is being *sent* and *yielded*.
 * Delegate item transmission to other coroutines by simply passing them the
   asynchronous generator endpoint.
 
See the documentation further details.
