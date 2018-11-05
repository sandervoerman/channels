# Python iterator streams between coroutines

This module provides a simple and easy to use `Channel` class to stream objects
between coroutines.

## Installation

Install the [sav.channels](https://pypi.org/project/sav.channels/) package from
the Python Package Index. See [installing packages](https://packaging.python.org/tutorials/installing-packages/) for further instruction.

## Usage

Every channel object consists of a `sender` and a `receiver`:

```python
from typing import AsyncIterator
from sav.channels import AsyncItemizer, Channel

channel = Channel()
sender: AsyncItemizer[str] = channel.sender
receiver: AsyncIterator[str] = channel.receiver
```

### Receiver

The `receiver` is an [asynchronous iterator](https://docs.python.org/3/glossary.html#term-asynchronous-iterator).
Use the `async for` syntax to read from it:

```python
async def read(receiver: AsyncIterable[str]) -> None:    
    async for item in receiver:
        print(item)      
```

You can use the receiver as the source for a generator pipeline:

```python
async def foo(receiver: AsyncIterable[Bar]) -> AsyncIterator[Baz]:
    y = None
    async for x in receiver:
        try:
            y.apply(x)
        except AttributeError:
            y = Baz(x)
        except GetOnWithIt:
            yield y
```

### Sender

The `sender` is the other end of the channel. Given that the receiver is an iterator, what type of object should the sender be? It is not a reverse iterator, not a generator, and not even a reverse generator. Let us call it an *itemizer*, because it turns objects into items. The `sav.channels` module provides the generic type alias `AsyncItemizer` which you can use to contravariantly annotate functions that operate on a sender object.

While generator pipelines are awesome, they do need a data source to *pull* from - a file, or a list, or another generator function containing `yield` statements. But what if you would like to *push* objects into the pipeline? You can try to organize the control flow of your program in such a way that every place where you need to write to the pipeline becomes another generator function, but then you lose a lot of flexibility. You can change your generator pipeline into a reverse generator pipeline, but then you've sacrificed the ability to *pull* data at all - including straightforward iteration. Or you could push your data into a buffer first, and then pull from it, but then you introduce latency and memory inefficiencies that should be unnecessary in the case of cooperative point-to-point message passing.

This is where `sender` comes in. We use the `async with` syntax to open the channel for writing and to make sure that it will be closed afterwards:

```python
async with sender as itemize:
    await itemize("One")
    await itemize("Two")
    await baz(itemize) # pass the itemizer to another coroutine
    await itemize("The end")
```

The `itemize` function behaves more or less like a `yield` statement in a generator: it passes a value to the receiver and waits for the receiver to iterate over it in the `async for` loop. When execution flows off the bottom of the `async with` block, control passes back to the receiver again, which will raise the `StopAsyncIteration` signal to exit from the `async for` loop. This is exactly how a generator function behaves - except that the `itemize` function (and it is your variable to name so you can call it whatever you want) can be passed around as a callback to any coroutine that needs writing access to the channel.

### Further details

See the test script for a full example and the module code for the full interface, including contravariant generic types for the context manager and callback function.
