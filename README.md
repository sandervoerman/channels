# Python iterator streams between coroutines

This module provides a simple and easy to use `Channel` class to stream objects
between coroutines. Every channel object consists of a `sender` and a `receiver`. The `receiver` is an asynchronous iterator. No special syntax, no new methods to learn. Use the `async for` syntax to read from it:

```python
channel = Channel()
async def read():    
    async for item in channel.receiver:
        print(item)      
```

You can use the receiver as the source for a generator pipeline:

```python
async def foo():    
    async for x in channel.receiver:
        yield bar(x)
```

So what about the `sender`? While generator pipelines are awesome, they do need a data source to *pull* from - a file, or a list, or another generator function containing `yield` statements. But what if you would like to *push* objects into the pipeline? You can try to organize the control flow of your program in such a way that every place where you need to write to the pipeline becomes another generator function, but then you lose a lot of flexibility. You can change your generator pipeline into a reverse generator pipeline, but then you've sacrificed the ability to *pull* data at all - including straightforward iteration. Or you could push your data into a buffer first, and then pull from it, but then you introduce latency and memory inefficiencies that should be unnecessary in the case of cooperative point-to-point message passing.

This is where `sender` comes in. We use the `async with` syntax to open the channel for writing and to make sure that it will be closed afterwards:

```python
async with c.sender as itemize:
    await itemize("One")
    await itemize("Two")
    await baz(itemize) # pass the itemizer to another coroutine
    await itemize("The end")
```

The `itemize` function behaves more or less like a `yield` statement in a generator: it passes a value to the receiver and waits for the receiver to iterate over it in the `async for` loop. When execution flows off the bottom of the `async with` block, control passes back to the receiver again, which will raise the `StopAsyncIteration` signal to exit from the `async for` loop. This is exactly how a generator function behaves - except that the `itemize` function (and it is your variable to name so you can call it whatever you want) can be passed around as a callback to any coroutine that needs writing access to the channel.

See the test script for a full example and the module code for the full interface, including contravariant generic types for the context manager and callback function.
