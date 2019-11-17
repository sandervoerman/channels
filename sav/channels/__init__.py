"""Channels between coroutines.

What is a channel?
==================
A channel is a pair of asynchronous generators, such that objects which
are sent into one of them will be yielded by the other, and vice-versa.

The purpose of channels is synchronization: every time the receiving
routine tries to pull an object out of a channel, its execution is
suspended until another routine sends an object into that channel, at
which point the receiving routine resumes.

Influential concurrent languages like CSP_, occam_ and Go_ have adopted
channels as a fundamental construct in their concurrency model. In the
case of Python, a similar concurrency model was built into the language
with the introduction of generators (:pep:`255`) and their further
development into coroutines (:pep:`342`, :pep:`380`, :pep:`492`) and
asynchronous generators (:pep:`525`).

.. _CSP: http://www.usingcsp.com/
.. _occam: http://www.wotug.org/occam/
.. _Go: https://tour.golang.org/concurrency/2


Channels versus generator functions
-----------------------------------
Like channels, generators are generic streams that alternatingly suspend
and resume routines at both ends of the stream. In the case of a
generator, however, one end of the stream is always tied to the
generator function, which is the only routine that can access the stream
from that end.

In the case of a channel, there are no ``yield`` expressions at either
end to communicate with the other end. That is why this package
implements channels for Python as a pair of generators: the yield
expressions are hidden inside the implementation, and the coroutines
at both ends of the channel interact with the methods of a generator
object.

Awaiting ``asend()`` from one end always blocks until a second caller
awaits ``asend()`` from the other end, establishing a rendez-vous
between the two awaiting coroutines. The value sent by the second
caller is then scheduled to be returned to the first caller. This
creates the same back-and-forth synchronization pattern that a generator
would create, with the added flexibility that you can send values into
different channels from the same coroutine.


Channels versus queues
----------------------
Note that this is also what distinguishes a channel from a queue. The
very idea of a queue is that it allows multiple consumers to call for
a next item before one is actually pushed into it by a producer, or
for multiple producers to send items into it before one is actually
picked up by a consumer. Therefore, duplexing over a single ``asend()``
method is impossible for a queue, because it would not be able to
tell from which end it is being called.

By contrast, a channel object simply assumes that it won't be called
again from the direction in which it has blocked the previous caller,
so whoever calls next should be calling from the other end. Thus, a
channel is *by contract* a point-to-point synchronization primitive.

Note that this does not restrict your code to calling the same channel
from the same end in different coroutines. Rather, the restriction is
that those coroutines won't be making those calls concurrently. If that is
your purpose, you should be using a queue.


The purpose of channels
=======================

Using a channel to push into a pipeline
---------------------------------------
If a value is sent into the channel from one end, it is returned at the
other end. Which means you can pass the channel to your own asynchronous
generator function, and have that function pull values out of the
channel, process them, and yield the results to another generator down
your processing pipeline. From the perspective of this pipeline, the
channel simply behaves like an upstream generator.

Nevertheless, every time the pipeline requests another item from the
channel, the producer coroutine resumes execution. This means that from
the perspective of the producer, it is interacting with a *reverse*
generator. Channels give you the power of reverse generator pipelines
without actually having to write reverse generator functions.

Furthermore, if you are working with bidirectional asynchronous
generators, then you are no longer limited by the requirement that all
your generator functions must have their yield expressions oriented in
the same way towards the dataflow in order to be part of the same
pipeline.


Refactoring generators into producers and vice-versa
----------------------------------------------------
The context manager of a channel is designed to mirror the body of an
asynchronous generator function::

    async with channels.open(ch):
        a = await ch.asend('One')
        b = await ch.asend('Two')
        c = await ch.asend('Three')

    async def ag():
        a = yield 'One'
        b = yield 'Two'
        c = yield 'Three'

This resemblance between channels and generator functions allows easy
refactoring. For example, when there is only one coroutine sending
values into a channel, and it does not do anything else besides that (as
in the example above), it should be changed into an asynchronous
generator function. On the other hand, there are certain limitations that
asynchronous generator functions have which can make them unwieldy. If
more and more functions need to be turned into generator functions
because they need to ``yield`` to other generators, or if the code is
full of ``while True: f((yield))`` loops instead of ``async for x: f(x)``
loops, refactoring generator functions into channels may be desirable.


Pushing into multiple channels from a single routine
----------------------------------------------------
Channels allow greater flexibility because you can send values into
different channels from within a single function or loop, whereas an
asynchronous generator function shares the limitation with synchronous
generators that it can only yield to the same generator object.


Efficient delegation to another producer
----------------------------------------
Asynchronous generator functions do not support ``yield from g`` in
order to delegate to another generator. Instead, you have to write
``async for x in g: yield x`` (in the simplex case) which means that the
control flow has to jump in and out of the delegating generator every
time before it jumps into the producing generator. By contrast, the
object returned by a channel when you use ``async with`` may be passed
onward to delegate production to another coroutine.


Bidirectional data flows
========================
The following example demonstrates how data flows through the
channel in the case of bidirectional communication::

    import asyncio
    import itertools
    from typing import AsyncGenerator
    from sav import channels

    async def numbers(c: AsyncGenerator[str, int]) -> None:
        async with channels.open(c):     # don't wait
            print(await c.asend(None))   # receive only
            for i in itertools.count():
                print(await c.asend(i))  # send and receive

    async def letters(c: AsyncGenerator[int, str]) -> None:
        async with channels.open(c):     # wait
            print(await c.asend("A"))    # send and receive
            print(await c.asend("B"))    # send and receive

    async def main() -> None:
        c_left, c_right = channels.create()
        await asyncio.gather(numbers(c_left), letters(c_right))

    asyncio.run(main())

This will produce the result::

    A
    0
    B
    1


The API
=======

Creating channels
-----------------

.. autofunction: create

Each generator will wait, when first iterated over, until the other is
first iterated over as well. The second generator is then scheduled to
yield None, while the first generator keeps waiting for a value to be
sent into the second generator.

From that point onwards, the channel operates symmetrically and
bidirectionally: when one generator is suspended, the other one is
waiting, and when a value is sent into the suspended generator, the
waiting generator is scheduled to yield that value.

When one of the two generators is closed, the other generator will be
scheduled to raise StopAsyncIteration.


Opening and closing generator connections
-----------------------------------------

.. autofunction: open

While asynchronous iteration only requires a single line of code,
connecting to a *reverse* or *bidirectional* asynchronous generator
typically involves several lines of boilerplate code. The following
example shows how you might need eight lines of code to send a
single message into a generator::

    try:                               # connect to a generator
        ag = my_ag()                       # create it
        await ag.asend(None)               # start it
        await ag.asend('Hello world!')     # send it a message
    except StopAsyncIteration:         # when it returns
        pass                               # clear exception
    finally:                           # when it keeps running
        await ag.aclose()                  # close it


With channels.open() this example may be rewritten as follows::

    async with channels.open(my_ag()) as ag:
        await ag.asend('Hello world!')

"""
from __future__ import annotations
from asyncio import get_running_loop
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Tuple, TypeVar

__all__ = ['create', 'open']

_AG = TypeVar('_AG', bound=AsyncGenerator)


def create() -> Tuple[AsyncGenerator, AsyncGenerator]:
    """Create a new channel.

    :returns: The pair of connected asynchronous generators.
    """

    fut = None

    async def generate(wait: bool) -> AsyncGenerator:
        nonlocal fut
        try:
            if fut is not None:
                fut.set_result((yield) if wait else None)

            f = get_running_loop().create_future
            while True:
                item = await (fut := f())
                fut.set_result((yield item))

        except EOFError:
            pass

        except GeneratorExit:
            if fut is not None:
                fut.set_exception(EOFError)

    return generate(False), generate(True)


@asynccontextmanager
async def open(ag: _AG, *, start: bool = True, clear: bool = True,
               close: bool = True) -> AsyncGenerator[_AG, None]:
    """Use a context manager to start and close a generator.

    :param ag: The async generator.
    :param start: Whether the generator should be started.
    :param clear: Whether StopAsyncIteration should be cleared.
    :param close: Whether the generator should be closed.
    :returns: The async context manager.
    """

    try:
        if start:
            await ag.asend(None)
        yield ag

    except StopAsyncIteration:
        if not clear:
            raise

    finally:
        if close:
            await ag.aclose()
