Overview
========

.. currentmodule:: sav

To use the module, import :mod:`channels` from the :mod:`sav` namespace
into an :mod:`asyncio` application. The module contains two functions,
:func:`channels.create` and :func:`channels.open`. The following example
demonstrates how they are used:

.. literalinclude:: example1.py

Channels are created by calling :func:`channels.create`:

   .. autofunction:: sav.channels.create


In the example, the first generator of each channel is simply iterated
over with an ``async for`` loop. The second generator may be started and
closed using ``async with`` and :func:`channels.open`:

   .. autofunction:: sav.channels.open

The ``async with`` statement waits until the ``async for`` loops at the
other ends of both channels are started, after which each second
endpoint is ready to send.

When control flows out of the ``async with`` block, the context
managers close the generators and schedules their counterparts at the
``async for`` ends of the channels to  raise :exc:`StopAsyncIteration`.
