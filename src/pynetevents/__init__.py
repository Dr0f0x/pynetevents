# The MIT License (MIT)
#
# Copyright (c) 2025 Dominik Czekai
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
PyNetEvents - A simple and flexible event system for Python.

This package provides an event-driven programming framework that allows you to
create event slots and attach multiple listeners (both synchronous and asynchronous)
to them. When events are fired, all registered listeners are notified.

Features:
- Support for both synchronous and asynchronous event handlers
- Simple subscription/unsubscription API with operator overloading
- Thread-safe event handling
- Automatic error handling and logging for event listeners

Example:
    >>> from pynetevents import EventSlot
    >>>
    >>> # Create an event slot
    >>> on_data_received = EventSlot("data_received")
    >>>
    >>> # Add listeners
    >>> def sync_handler(data):
    ...     print(f"Received: {data}")
    >>>
    >>> async def async_handler(data):
    ...     print(f"Async received: {data}")
    >>>
    >>> on_data_received += sync_handler
    >>> on_data_received += async_handler
    >>>
    >>> # Fire the event
    >>> on_data_received("Hello, World!")
"""

from .events import EventSlot, EventsException, Event

__all__ = [
    "EventSlot",
    "Event",
    "EventsException",
]

__version__ = "0.1.1"
