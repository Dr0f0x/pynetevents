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

from abc import ABC
import asyncio
import inspect
import weakref
from typing import Any, Callable, Iterator, List, Optional
import logging

logger = logging.getLogger()


class _EventSlotBase(ABC):
    """Base class for EventSlot implementations."""

    def __init__(
        self,
        name: Optional[str] = None,
        propagate_exceptions: Optional[bool] = None,
        allow_duplicate_listeners: Optional[bool] = None,
    ):
        self.name = name
        # If a flag is None, use EventSlot's default but record that it was defaulted.
        if propagate_exceptions is None:
            self.propagate_exceptions: bool = True
            self.propagate_exceptions_was_default: bool = True
        else:
            self.propagate_exceptions = propagate_exceptions
            self.propagate_exceptions_was_default: bool = False

        if allow_duplicate_listeners is None:
            self.allow_duplicate_listeners: bool = False
            self.allow_duplicate_listeners_was_default: bool = True
        else:
            self.allow_duplicate_listeners = allow_duplicate_listeners
            self.allow_duplicate_listeners_was_default: bool = False

        self._listeners: List[Callable[..., Any]] = []

        # Hold references to created asyncio tasks to prevent them being
        # garbage-collected before they start running.
        self._tasks: List[asyncio.Task] = []

    def __repr__(self) -> str:
        return f"EventSlot('name={self.name}, listeners={len(self._listeners)}')"

    def invoke(self, *args, **kwargs) -> None:
        """
        Invoke all listeners passing the given args and kwargs. Synchronous
        listeners are called directly, while asynchronouslisteners are
        scheduled (fire and forget).
        """
        dead_listeners = []

        for listener in self._listeners:
            listener_exc = self.__get_executable_listener(listener)

            if listener_exc is None:
                dead_listeners.append(listener)
                continue

            try:
                if inspect.iscoroutinefunction(listener_exc):
                    task = asyncio.create_task(listener_exc(*args, **kwargs))
                    # Keep a reference to prevent premature garbage collection.
                    self._tasks.append(task)
                    # Remove the task from the list when done to avoid memory leaks.
                    task.add_done_callback(
                        lambda t: self._tasks.remove(t) if t in self._tasks else None
                    )
                else:
                    listener_exc(*args, **kwargs)
            except Exception as e:  # pylint: disable=broad-except
                if self.propagate_exceptions:
                    raise EventExecutionError(
                        f"Error in listener for event '{self.name}': {e}",
                    ) from e
                logger.error(
                    "Error in listener for event '%s': %s",
                    self.name,
                    e,
                )

        if dead_listeners:
            self._listeners = [l for l in self._listeners if l not in dead_listeners]

    def __get_executable_listener(self, listener: Any) -> Callable[..., Any]:
        """Get the actual callable from a listener, handling weak references."""
        if isinstance(listener, weakref.WeakMethod):
            func = listener()
            return func
        return listener

    async def invoke_async(self, *args: Any, **kwargs: Any) -> None:
        """
        Invoke all listeners passing the given args and kwargs, awaiting coroutine functions and
        calling normal functions synchronously.
        """
        dead_listeners = []
        for listener in self._listeners:
            listener_exc = self.__get_executable_listener(listener)

            if listener_exc is None:
                dead_listeners.append(listener)
                continue
            try:
                if inspect.iscoroutinefunction(listener_exc):
                    # Await the coroutine
                    await listener_exc(*args, **kwargs)
                else:
                    # Call synchronous functions normally
                    listener_exc(*args, **kwargs)
            except Exception as e:  # pylint: disable=broad-except
                if self.propagate_exceptions:
                    raise EventExecutionError(
                        f"Error in listener for event '{self.name}': {e}",
                    ) from e
                logger.error(
                    "Error in listener for event '%s': %s",
                    self.name,
                    e,
                )

        if dead_listeners:
            self._listeners = [l for l in self._listeners if l not in dead_listeners]

    def _subscribe(
        self, listener: Callable[..., Any], use_weakref: bool = False
    ) -> None:
        """Add a listener to the event slot, potentially using a weakref."""

        if use_weakref and inspect.ismethod(listener):
            listener = weakref.WeakMethod(listener)

        if not self.allow_duplicate_listeners:
            if listener not in self._listeners:
                self._listeners.append(listener)
            else:
                raise EventExecutionError(
                    f"Listener {listener} is already subscribed to event '{self.name}'. \
                        (you can allow this by setting allow_duplicate_listeners=True)"
                )
        else:
            self._listeners.append(listener)

    def _unsubscribe(
        self, listener: Callable[..., Any], use_weakref: bool = False
    ) -> None:
        """Remove a listener from the event slot, handling weakrefs if needed."""
        if use_weakref and inspect.ismethod(listener):
            # Remove matching WeakMethod references
            self._listeners = [
                l
                for l in self._listeners
                if not (isinstance(l, weakref.WeakMethod) and l() == listener)
            ]

        # Remove direct strong references
        self._listeners = [l for l in self._listeners if l != listener]

    def subscribe(self, listener: Callable[..., Any]) -> None:
        """Add a listener to the event slot."""
        self._subscribe(listener, use_weakref=False)

    def unsubscribe(self, listener: Callable[..., Any]) -> None:
        """Remove a listener from the event slot."""
        self._unsubscribe(listener, use_weakref=False)

    def subscribe_weak(self, listener: Callable[..., Any]) -> None:
        """Add a listener to the event slot using a weak reference."""
        self._subscribe(listener, use_weakref=True)

    def unsubscribe_weak(self, listener: Callable[..., Any]) -> None:
        """Remove a listener from the event slot that was added using a weak reference."""
        self._unsubscribe(listener, use_weakref=True)

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

    def __getstate__(self):
        """Forbid pickling"""
        raise NotImplementedError("EventSlots cannot be pickled or unpickled")

    def __setstate__(self, state):
        raise NotImplementedError("EventSlots cannot be pickled or unpickled")


class EventSlot(_EventSlotBase):
    """A slot to which callbacks can be attached and fired; += and
    -= use strong references for listeners."""

    # Operator overloads for convenience
    def __iadd__(self, listener: Callable[..., Any]) -> "EventSlot":
        """Adds a listener, used by the '+=' operator."""
        self.subscribe(listener)
        return self

    def __isub__(self, listener: Callable[..., Any]) -> "EventSlot":
        """Removes a listener, used by the '-=' operator."""
        self.unsubscribe(listener)
        return self


class EventSlotWeakRef(_EventSlotBase):
    """A slot to which callbacks can be attached and fired; += and
    -= use weak references for listeners."""

    # Operator overloads for convenience
    def __iadd__(self, listener: Callable[..., Any]) -> "EventSlot":
        """Adds a listener, used by the '+=' operator."""
        self.subscribe_weak(listener)
        return self

    def __isub__(self, listener: Callable[..., Any]) -> "EventSlot":
        """Removes a listener, used by the '-=' operator."""
        self.unsubscribe_weak(listener)
        return self


class Event:
    """Descriptor for event slots in classes."""

    def __init__(
        self,
        propagate_exceptions: Optional[bool] = None,
        allow_duplicate_listeners: Optional[bool] = None,
        use_weakref_slot: Optional[bool] = None,
    ):
        self.__name: Optional[str] = None
        self.propagate_exceptions: Optional[bool] = propagate_exceptions
        self.allow_duplicate_listeners: Optional[bool] = allow_duplicate_listeners
        self.use_weakref_slot: Optional[bool] = use_weakref_slot

    @property
    def name(self) -> str:
        """Get the name of the event."""
        return self.__name

    def __set_name__(self, owner, name):
        """Automatically set the event name from the attribute name if not given."""
        self.__name = name

    def __param_consistency_check(self, instance, existing: EventSlot) -> None:
        """Check that the existing EventSlot matches the declared parameters."""
        problems = []
        if (
            self.propagate_exceptions is not None
            and not existing.propagate_exceptions_was_default
            and existing.propagate_exceptions != self.propagate_exceptions
        ):
            problems.append("propagate_exceptions")
        if (
            self.allow_duplicate_listeners is not None
            and not existing.allow_duplicate_listeners_was_default
            and existing.allow_duplicate_listeners != self.allow_duplicate_listeners
        ):
            problems.append("allow_duplicate_listeners")
        if (
            self.name is not None
            and existing.name is not None
            and existing.name != self.name
        ):
            problems.append("name")
        if (
            self.use_weakref_slot is not None
            and isinstance(existing, EventSlotWeakRef) != self.use_weakref_slot
        ):
            problems.append("weakref_slot")

        if problems:
            raise AttributeError(
                f"EventSlot '{self.name}' on {type(instance)!r} has inconsistent parameters \
                    compared to declared event descriptor. (existing: name={existing.name} \
                    propagate_exceptions={existing.propagate_exceptions}, \
                    allow_duplicate_listeners={existing.allow_duplicate_listeners}; \
                    weakref_slot={isinstance(existing, EventSlotWeakRef)}; "
                f"declared: name={self.name} propagate_exceptions={self.propagate_exceptions}, \
                    allow_duplicate_listeners={self.allow_duplicate_listeners}) \
                    weakref_slot={self.use_weakref_slot}."
            )

        # assign desciptor parameters to existing slot if they were defaulted
        if self.propagate_exceptions is not None:
            existing.propagate_exceptions = self.propagate_exceptions
        if self.allow_duplicate_listeners is not None:
            existing.allow_duplicate_listeners = self.allow_duplicate_listeners
        existing.name = self.name

    def __get__(self, instance, owner) -> "EventSlot":
        """Get the event slot for the instance."""

        existing = instance.__dict__.get(self.name)
        if existing is not None:
            return existing

        # create a new EventSlot and store it in the instance dict
        kwargs = {}
        if self.propagate_exceptions is not None:
            kwargs["propagate_exceptions"] = self.propagate_exceptions
        if self.allow_duplicate_listeners is not None:
            kwargs["allow_duplicate_listeners"] = self.allow_duplicate_listeners

        if self.use_weakref_slot is not None and self.use_weakref_slot:
            new_slot = EventSlotWeakRef(self.name, **kwargs)
        else:
            new_slot = EventSlot(self.name, **kwargs)

        instance.__dict__[self.name] = new_slot
        return new_slot

    def __set__(self, instance, value) -> None:
        """
        Allow only assignment that comes from in-place operations:
        - If value is the same Event instance accept (no-op), otherwise, forbid reassignment.
        """

        # Accept if user assigns back the exact event object (from +=/-=)
        current_slot = instance.__dict__.get(self.name)
        if value is current_slot:
            return
        if current_slot is None:
            if isinstance(value, EventSlot):
                self.__param_consistency_check(instance, value)
                instance.__dict__[self.name] = value
                return
            raise TypeError(
                f"Tried to assign a non-EventSlot value to event attribute '{self.name}'\
                        on {type(instance)!r} "
                f"(found {type(value)!r})."
            )

        raise AttributeError(
            f"Event '{self.name}' can only be modified via '+=' or '-=' operations. (or set to "
            + "modified versions of same instance)",
        )


class EventExecutionError(Exception):
    """Base exception class for events-related errors."""
