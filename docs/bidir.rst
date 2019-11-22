Bidirectional channels
======================

.. currentmodule:: sav

The following example shows how to use a channel bidirectionally:

.. literalinclude:: example2.py

In this case, :func:`channels.open` is used to set up ``async with``
blocks at both ends of the channel.

The first endpoint always starts receiving. Therefore, it is opened
with ``start=False``, and must be started manually by sending `None`
in order to await the first value from the second end.

The second endpoint waits until the first endpoint has been started.

From that point onwards, the channel operates symmetrically: when one
generator is suspended, the other one is waiting, and when a value is
sent into the suspended generator, the waiting generator is scheduled
to yield that value.

When one of the two generators is closed, the other generator will be
scheduled to raise :exc:`StopAsyncIteration`. Although there is no
``async for`` loop in this case, :func:`channels.open` will clear the
:exc:`StopAsyncIteration` exception when it reaches the end of the
``async with`` block. In this way, the bidirectional usage elegantly
resembles the unidirectional usage: when one of the two ``async with``
blocks is exited, the other one will be exited as well.
