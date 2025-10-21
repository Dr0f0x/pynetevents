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

    def __repr__(self) -> str:
        return f"EventSlot('{self.name}')"

    def __call__(self, *args, **kwargs) -> None:
        """Fire the event, calling all listeners."""
        for listener in list(self._listeners):

            try:
                if inspect.iscoroutinefunction(listener):
                    asyncio.create_task(listener(*args, **kwargs))
                else:
                    listener(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Error in listener for event '{self.name}': {e}")

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
        self.subscribe(listener)
        return self

    def __isub__(self, listener: Callable[..., Any]) -> "EventSlot":
        self.unsubscribe(listener)
        return self

    def __len__(self) -> int:
        return len(self._listeners)

    def __iter__(self) -> Iterator[Callable[..., Any]]:
        return iter(self._listeners)

    def __getitem__(self, index: int) -> Callable[..., Any]:
        return self._listeners[index]


class EventsException(Exception):
    pass
