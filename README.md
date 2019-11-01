# Channels: Python iterator streams between coroutines

This package provides a simple and easy to use `Channel` class to send and
receive objects between coroutines.

Version 0.5, copyright &copy; [Sander Voerman](sander@savoerman.nl), 2019.


## Installation

Install the [sav.channels](https://pypi.org/project/sav.channels/)
package from the Python Package Index. See
[installing packages](https://packaging.python.org/tutorials/installing-packages/)
for further instruction.

## Overview

A channel is a direct connection between two coroutines, through which they can
send and receive objects. Channels are similar to asynchronous generators, 
except that you don't need `yield` expressions at either end of a channel to 
communicate with the other end.

### Example

Suppose you have two coroutines running `async for` loops:
 
```python
async def loop_a(a_items):
    async for a_item in a_items:
        ...

async def loop_b(b_items):
    async for b_item in b_items:
        ...
```

In order to feed the first loop with items, you write the following generator
function. At some point, this function also produces an item for the second
loop. You would like that loop to resume as soon as the item becomes available: 

```python
async def gen():
    yield 'This is the first a-item.'  # yield to loop_a
    'This is the first b-item'         # need to "yield" this to loop_b
    yield 'This is another a-item.'
```

You can solve this problem with a channel:

```python
from asyncio import gather, run
from sav.channels import Channel

async def loop_a(a_items):
    ...

async def loop_b(b_items):
    ...

async def gen(chan):
    async with chan:
        yield 'This is the first a-item.'
        await chan.asend('This is the first b-item')
        yield 'This is another a-item.'

async def main():
    chan = Channel()
    await gather(loop_a(gen(chan)), loop_b(chan))

run(main())
```

### Features

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
   for every single item (`StreamChannel` class).
 * Delegate item transmission to synchronous generators and read from them in
   the receiving coroutine (`StreamChannel` class).
 
See the documentation in the source code for further details and examples.
