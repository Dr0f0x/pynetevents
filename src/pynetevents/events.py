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
Event system implementation for Python applications.

This module provides a simple and flexible event system that allows you to create
event slots that can have multiple listeners (both synchronous and asynchronous)
attached to them. When an event is fired, all attached listeners are called.

Classes:
    EventSlot: A slot to which callbacks can be attached and fired.
    Event: Descriptor for event slots in classes to restrict access to the event system.
    EventsException: Base exception class for events-related errors.
"""

import asyncio
import inspect
from typing import Any, Callable, Iterator, List
import logging

logger = logging.getLogger()


class EventSlot:
    """A slot to which callbacks can be attached and fired."""

    def __init__(self, name: str):
        self.name: str = name
        self._listeners: List[Callable[..., Any]] = []

        # Hold references to created asyncio tasks to prevent them being
        # garbage-collected before they start running.
        self._tasks: List[asyncio.Task] = []

    def __repr__(self) -> str:
        return f"EventSlot('{self.name}')"

    def invoke(self, *args, **kwargs) -> None:
        """
        Invoke all listeners passing the given args and kwargs. Synchronous
        listeners are called directly, while asynchronouslisteners are
        scheduled (fire and forget).
        """
        for listener in self._listeners:

            try:
                if inspect.iscoroutinefunction(listener):
                    task = asyncio.create_task(listener(*args, **kwargs))
                    # Keep a reference to prevent premature garbage collection.
                    self._tasks.append(task)
                    # Remove the task from the list when done to avoid memory leaks.
                    task.add_done_callback(
                        lambda t: self._tasks.remove(t) if t in self._tasks else None
                    )
                else:
                    listener(*args, **kwargs)
            except Exception as e:
                raise EventsException(
                    f"Error in listener for event '{self.name}': {e}",
                ) from e

    async def invoke_async(self, *args: Any, **kwargs: Any) -> None:
        """
        Invoke all listeners passing the given args and kwargs, awaiting coroutine functions and
        calling normal functions synchronously.
        """
        for listener in self._listeners:
            try:
                if inspect.iscoroutinefunction(listener):
                    # Await the coroutine
                    await listener(*args, **kwargs)
                else:
                    # Call synchronous functions normally
                    listener(*args, **kwargs)
            except Exception as e:
                raise EventsException(
                    f"Error in listener for event '{self.name}': {e}",
                ) from e

    def subscribe(self, listener: Callable[..., Any]) -> None:
        """Add a listener to the event slot."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[..., Any]) -> None:
        """Remove a listener from the event slot."""
        while listener in self._listeners:
            self._listeners.remove(listener)

    # Operator overloads for convenience
    def __iadd__(self, listener: Callable[..., Any]) -> "EventSlot":
        """Adds a listener, used by the '+=' operator."""
        self.subscribe(listener)
        return self

    def __isub__(self, listener: Callable[..., Any]) -> "EventSlot":
        """Removes a listener, used by the '-=' operator."""
        self.unsubscribe(listener)
        return self

    # dunder methods
    def __call__(self, *args, **kwds) -> None:
        """Invoke the event slot, calling all listeners with the passed args."""
        self.invoke(*args, **kwds)

    def __len__(self) -> int:
        """Return the number of listeners attached to the event slot."""
        return len(self._listeners)

    def __iter__(self) -> Iterator[Callable[..., Any]]:
        """Return an iterator over the listeners attached to the event slot."""
        return iter(self._listeners)

    def __getitem__(self, index: int) -> Callable[..., Any]:
        """Get a listener by index."""
        return self._listeners[index]


class Event:
    """Descriptor for event slots in classes."""

    def __init__(self, name: str | None = None):
        self.name = name
        self._instance_slots = {}

    def __set_name__(self, owner, name):
        """Automatically set the event name from the attribute name if not given."""
        if self.name is None:
            self.name = name

    def __get__(self, instance, owner):
        """Get the event slot for the instance."""
        if instance is None:
            return self  # Accessed on the class

        # Lazily create per-instance slot
        if instance not in self._instance_slots:
            new_slot = EventSlot(self.name)
            self._instance_slots[instance] = new_slot
            return new_slot
        return self._instance_slots[instance]

    def __set__(self, instance, value) -> None:
        """
        Allow only assignment that comes from in-place operations:
        - If value is the same Event instance accept (no-op), otherwise, forbid reassignment.
        """

        # Accept if user assigns back the exact event object (from +=/-=)
        current_slot = self._instance_slots.get(instance)
        if value is current_slot:
            return

        raise AttributeError(
            f"Event '{self.name}' can only be modified via '+=' or '-=' operations. (or set to "
            + "modified versions of same instance)",
        )


class EventsException(Exception):
    """Base exception class for events-related errors."""
