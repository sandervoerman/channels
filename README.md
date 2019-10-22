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
send and receive objects.

### Simplex example

Every channel consists of a client and a server end. In the case where objects
are sent in only one direction, the `client()` method returns the receiving
end, which can be iterated over using `async for`. The `server` method returns
a context manager that can be opened and closed using `async with` in the
producing coroutine:

```python
import asyncio
from typing import AsyncIterator, AsyncGenerator
from sav.channels import Channel
from foo import Foo

async def produce(channel: Channel[Foo, None]) -> None:
    async with channel.server() as server:
        await server.asend(Foo("One"))
        await produce_two(server)
        await server.asend(Foo("Three"))

async def produce_two(server: AsyncGenerator[None, Foo]) -> None:
    await server.asend(Foo("Two"))

async def consume(client: AsyncIterator[Foo]) -> None:    
    async for foo in client:
        print(foo)      

async def main() -> None:
    channel = Channel()
    await asyncio.gather(consume(channel.client()), produce(channel))

asyncio.run(main())
```

### Duplex example

The objects returned by `channel.client()` and `async with channel.server()`
are both [asynchronous generators](https://www.python.org/dev/peps/pep-0525/)
which support communication in both directions. The following example
demonstrates how data flows through the channel in both directions:

```python
import asyncio
import itertools
from sav.channels import Channel

async def letters(channel: Channel[str, int]) -> None:
    async with channel.server() as s:            # wait for the client
        print(await s.asend("A"))    # send and receive
        print(await s.asend("B"))    # send and receive

async def numbers(channel: Channel[str, int]) -> None:
    asend = channel.client().asend
    try:
        print(await asend(None))   # receive only
        for i in itertools.count():
            print(await asend(i))  # send and receive
    except StopAsyncIteration:
        pass

async def main() -> None:
    channel = Channel()
    await asyncio.gather(letters(channel), numbers(channel))

asyncio.run(main())
```

This will produce the result:

```
A
0
B
1
```

Hence, the first item to be sent through the channel is the one sent by the
server. The `async with` block starts the server by awaiting `asend(None)`,
which blocks until the client is started and waiting for the first item to
receive. When execution flows off the `async with` block, the server is
closed by awaiting `aclose()`, which causes the waiting client to raise
`StopAsyncIteration`.


## The purpose of channels

Although the possibility to send values in both directions can be useful in
certain situations, it is not what makes channels interesting, or why we need
them. The purpose of a channel lies in the fact that it reverses the
directions, so to speak, in which the client and server generators send and
yield values.

### Using a channel to push into a pipeline

If a value is sent into the server generator, it is yielded by
the client generator. Which means you can pass the client generator to your own
asynchronous generator function, and have that function pull values out of
the channel, process them, and yield the results to another generator down
your processing pipeline. Nevertheless, every time the pipeline requests
another item from the channel, the producer coroutine that was awaiting the
result from `server.asend` resumes execution. This means that from the perspective
of the producer, the pipeline looks like a *reverse* generator. Channels give
you the power of reverse generator pipelines without actually having to write
reverse generator functions.

### Refactoring generators into producers and vice-versa

The server context of a channel is designed to mirror the body of an
asynchronous generator function:

```python

async with chan.server() as s:
    a = await s.asend('One')
    b = await s.asend('Two')
    c = await s.asend('Three')

async def agen():
    a = yield 'One'
    b = yield 'Two'
    c = yield 'Three'

```

This resemblance between channels and generator functions allows easy
refactoring. For example, when there is only one coroutine sending values
into a channel, and it does not do anything else besides that (as in the
example above), it should
be changed into an asynchronous generator function. On the other hand,
there are certain limitations that asynchronous generator functions have
which can make them unwieldy. If more and more functions need to be turned
into generator functions because they need to `yield` to other generators,
or if the code is full of `while True: f((yield))` loops instead of
`async for x: f(x)` loops, refactoring generator functions into channels
may be desirable.

### Pushing into multiple channels from a single routine

Channels allow greater flexibility because you can send values
into different channels from within a single function or loop, whereas an
asynchronous generator function shares the limitation with synchronous
generators that it can only yield to the same generator object.

### Efficient delegation to another producer

Asynchronous generator functions do not support `yield from g` in order
to delegate to another generator. Instead, you have to write
`async for x in g: yield x` (in the simplex case) which means that the event
loop has to jump in and out of the delegating generator every time
before it jumps into the producing generator, since the semantics of your
code requires that the value of `x` be updated on every iteration.
By contrast, the object returned by a channel when you use `async with` may
be passed onward to delegate production to another coroutine, as shown in the
first example at the top of this document.


## Combining asynchronous and synchronous iteration

The `StreamChannel` class provides additional reading and writing methods
that allow sending multiple items, or even synchronous unsized iterators,
through the channel without passing control back to the event loop for
every single item.