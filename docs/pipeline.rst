Channels and generator pipelines
================================
One powerful application of generators is that they may be used to
build generator pipelines. The following example shows how a channel
may be used to send values into such a pipeline from the upstream end.
In this case, the channel functions like a generator adapter, reversing
the directions in which data is being *sent* and *yielded*.

.. literalinclude:: example3.py
