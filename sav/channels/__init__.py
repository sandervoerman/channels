"""Point-to-point object streams between coroutines."""
from .futures import Channel
from .streams import StreamChannel

__ALL__ = ['Channel', 'StreamChannel']
