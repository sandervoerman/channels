# Channels between coroutines
A simple [Python] implementation of the [channel] synchronization
construct for [async/await] applications.

Channels are used for synchronization in the [CSP] concurrency model.
They are natively supported by languages that implement this model, such
as [occam] and [Go]. Python has [asynchronous generators], which are
similar to channels except that they require yielding instead of calling
from one of the two endpoints. While this makes no difference in many
cases, some problems are easier to solve if a data stream can be
accessed from both ends by calling instead of yielding.

The `sav.channels` module implements channels as pairs of
asynchronous generators. When an object is sent into one generator, it
will be yielded by the other generator, and vice-versa.


## Installation
This module requires Python 3.8 or higher. Use `pip` to install it
from the command line:

```
pip install sav.channels
```

Or visit the online project pages on [GitHub] and [PyPI].


## Example

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

## Documentation
See the [documentation] for further details.

Or use [Sphinx] to build a local copy of the documentation from the package
source:

```
cd docs
make singlehtml
```

[Python]: https://www.python.org/
[channel]: https://en.wikipedia.org/wiki/Channel_(programming)
[async/await]: https://www.python.org/dev/peps/pep-0492/
[CSP]: http://www.usingcsp.com/
[occam]: http://www.wotug.org/occam/
[Go]: https://tour.golang.org/concurrency/2
[asynchronous generators]: https://www.python.org/dev/peps/pep-0525/
[GitHub]: https://github.com/sandervoerman/channels
[PyPI]: https://pypi.org/project/sav.channels/
[documentation]: https://www.savoerman.nl/channels/
[Sphinx]: https://www.sphinx-doc.org/
