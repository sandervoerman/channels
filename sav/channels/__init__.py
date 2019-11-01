"""Channels between coroutines.

This package provides a simple and easy to use :class:`Channel` class to
send and receive objects between coroutines with async/await syntax.
It also provides a :class:`StreamChannel` class with methods for
synchronously reading, writing, or generating multiple items on the fly
during a single rendez-vous between the connected coroutines.


What is a channel?
==================
Channels are generic streams between routines that push objects into
those streams, and concurrently running routines that pull those objects
out again. The purpose of channels is synchronization: every time the
receiving routine tries to pull an object out of a channel, its
execution is suspended until another routine sends an object into that
channel, at which point the receiving routine resumes.

Influential concurrent languages like CSP_, occam_ and Go_ have adopted
channels as a fundamental construct in their concurrency model. In the
case of Python, a similar concurrency model was built into the language
with the introduction of generators (:pep:`255`) and their further
development into coroutines (:pep:`342`, :pep:`380`, :pep:`492`) and
asynchronous generators (:pep:`525`).

.. _CSP: http://www.usingcsp.com/
.. _occam: http://www.wotug.org/occam/
.. _Go: https://tour.golang.org/concurrency/2


Channels versus generators
--------------------------
Like channels, generators are generic streams that alternatingly suspend
and resume routines at both ends of the stream. In the case of a
generator, however, one end of the stream is always tied to the
generator function, which is the only routine that can access the stream
from that end.

In the case of a channel, there are no ``yield`` expressions at either
end to communicate with the other end. Instead, coroutines at both ends
await the same methods of the channel. These methods resemble those of
an asynchronous generator iterator, including ``asend()`` for sending
or duplexing and ``__aiter__()`` for asynchronous iteration. Thus, you
can run an ``async for`` loop at one end of a channel and call
``asend()`` from the other end to feed that loop.

Awaiting ``asend()`` from one end always blocks until a second caller
awaits ``asend()``, or one of the channel's other methods, establishing
a rendez-vous between the two awaiting coroutines. The value sent by the
second caller is then scheduled to be returned to the first caller. This
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
channel, the producer coroutine that was awaiting the result from
:meth:``Channel.asend`` resumes execution. This means that from the
perspective of the producer, the channel looks like a *reverse*
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

    async with ch:
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
event loop has to jump in and out of the delegating generator every time
before it jumps into the producing generator, since the semantics of
your code requires that the value of ``x`` be updated on every
iteration. By contrast, the object returned by a channel when you use
``async with`` may be passed onward to delegate production to another
coroutine.
"""

from .futures import Channel
from .streams import StreamChannel

__ALL__ = ['Channel', 'StreamChannel']
