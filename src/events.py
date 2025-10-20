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