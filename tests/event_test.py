"""
Tests for the EventSlot class in the pynetevents package.
"""

import asyncio
import pytest

from pynetevents import EventSlot
from pynetevents.events import EventsException


def test_invoke_sync_listener():
    """Test that invoke calls synchronous listeners immediately."""
    called = []

    def sync_listener(x):
        called.append(("sync", x))

    slot = EventSlot("test")
    slot.subscribe(sync_listener)
    slot.invoke("hello")

    assert called == [("sync", "hello")]


@pytest.mark.asyncio
async def test_invoke_async_listener_fire_and_forget():
    """Test that invoke schedules asynchronous listeners (fire-and-forget)."""
    called = []

    async def async_listener(x):
        await asyncio.sleep(1)
        called.append(("async", x))

    slot = EventSlot("test")
    slot.subscribe(async_listener)
    slot.invoke("hello")

    # Give async tasks time to run
    await asyncio.sleep(0.01)

    assert not called
    await asyncio.sleep(2)
    assert called == [("async", "hello")]


@pytest.mark.asyncio
async def test_invoke_async_awaits_all():
    """Test that invoke_async awaits async listeners and calls sync ones."""
    called = []

    def sync_listener(x):
        called.append(("sync", x))

    async def async_listener(x):
        await asyncio.sleep(1)
        called.append(("async", x))

    slot = EventSlot("test")
    slot += sync_listener
    slot += async_listener

    await slot.invoke_async("world")

    assert ("sync", "world") in called
    assert ("async", "world") in called


def test_subscribe_and_unsubscribe_methods():
    """Test subscribing and unsubscribing with the verbose methods."""
    called = []

    def listener(x):
        called.append(x)

    slot = EventSlot("test")
    slot.subscribe(listener)
    slot("msg1")
    assert called == ["msg1"]

    slot.unsubscribe(listener)
    slot("msg2")
    assert called == ["msg1"]  # listener removed


def test_iadd_isub_dunder_operators():
    """Test adding/removing listeners using += and -= operators."""
    called = []

    def listener(x):
        called.append(x)

    slot = EventSlot("test")
    slot += listener
    slot("event")
    assert called == ["event"]

    slot -= listener
    slot("event2")
    assert called == ["event"]  # listener removed


def test_no_duplicate_listeners():
    """Test that adding the same listener twice does not duplicate it."""
    called = []

    def listener(x):
        called.append(x)

    slot = EventSlot("test")

    # Add the same listener multiple times
    slot.subscribe(listener)
    slot.subscribe(listener)
    slot += listener
    slot += listener

    # There should only be one listener in the slot
    assert len(slot) == 1

    # Invoke it, should only be called once
    slot("event")
    assert called == ["event"]


@pytest.mark.asyncio
async def test_len_and_iter_with_listeners():
    """Test __len__ and __iter__ return correct values."""
    called = []

    def listener1(x):
        called.append(x)

    async def listener2(x):
        await asyncio.sleep(0)
        called.append(x)

    slot = EventSlot("test")
    slot += listener1
    slot += listener2

    assert len(slot) == 2
    listeners = list(iter(slot))
    assert listener1 in listeners
    assert listener2 in listeners


def test_getitem_returns_correct_listener():
    """Test that __getitem__ returns the listener at the given index."""
    called = []

    def listener1(x):
        called.append(("l1", x))

    def listener2(x):
        called.append(("l2", x))

    slot = EventSlot("test")
    slot += listener1
    slot += listener2

    # Check that __getitem__ returns the correct listener
    assert slot[0] is listener1
    assert slot[1] is listener2

    # Invoke via retrieved listener to ensure it's callable
    slot[0]("hello")
    slot[1]("world")
    assert called == [("l1", "hello"), ("l2", "world")]


def test_repr_returns_expected_string():
    """Test that __repr__ returns the correct string representation."""
    slot = EventSlot("my_event")
    assert repr(slot) == "EventSlot('my_event')"


def test_listener_propagates_exceptions():
    """Test that exceptions from listeners are properly caught and logged."""

    slot = EventSlot("test_exception")
    called = []

    def good_listener():
        called.append("good")

    def bad_listener():
        called.append("bad_before")
        raise ValueError("Test exception")

    slot += good_listener
    slot += bad_listener

    with pytest.raises(EventsException) as excinfo:
        slot()
    assert "Error in listener for event 'test_exception'" in excinfo.value.args[0]


@pytest.mark.asyncio
async def test_async_listener_propagate_exceptions():
    """Test that exceptions from async listeners are properly caught and logged."""

    slot = EventSlot("test_async_exception")
    called = []

    async def good_async_listener():
        called.append("good_async")

    async def bad_async_listener():
        called.append("bad_async_before")
        raise ValueError("Async test exception")

    slot += good_async_listener
    slot += bad_async_listener

    with pytest.raises(EventsException) as excinfo:
        await slot.invoke_async()
    assert "Error in listener for event 'test_async_exception'" in excinfo.value.args[0]
