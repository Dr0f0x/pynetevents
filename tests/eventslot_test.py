"""
Tests for the EventSlot class in the pynetevents package.
"""

import asyncio
from unittest.mock import Mock
import pytest

from pynetevents import EventSlot
from pynetevents.events import EventExecutionError

# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring


def test_invoke_sync_listener():
    called = []

    def sync_listener(x):
        called.append(("sync", x))

    slot = EventSlot("test")
    slot.subscribe(sync_listener)
    slot.invoke("hello")

    assert called == [("sync", "hello")]


@pytest.mark.asyncio
async def test_invoke_async_listener_fire_and_forget():
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


def test_duplicate_listeners_with_not_allowed_throws_exception():
    called = []

    def listener(x):
        called.append(x)

    slot = EventSlot("test")

    # Add the same listener multiple times
    slot.subscribe(listener)
    with pytest.raises(EventExecutionError) as excinfo:
        slot.subscribe(listener)
        slot += listener
        slot += listener
    assert "is already subscribed to event" in str(excinfo.value)

    # There should only be one listener in the slot
    assert len(slot) == 1

    # Invoke it, should only be called once
    slot("event")
    assert called == ["event"]


def test_allow_duplicate_listeners():
    called = []

    def listener(x):
        called.append(x)

    slot = EventSlot("test", allow_duplicate_listeners=True)

    # Add the same listener multiple times
    slot.subscribe(listener)
    slot.subscribe(listener)
    slot += listener

    # There should be three listeners in the slot
    assert len(slot) == 3

    # Invoke it, should be called three times
    slot("event")
    assert called == ["event", "event", "event"]


@pytest.mark.asyncio
async def test_len_and_iter_with_listeners():
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
    slot = EventSlot("my_event")
    assert "my_event" in repr(slot) and "listeners=0" in repr(slot)


def test_listener_with_propagate_true_propagates_exceptions():

    slot = EventSlot("test_exception")
    called = []

    def good_listener():
        called.append("good")

    def bad_listener():
        called.append("bad_before")
        raise ValueError("Test exception")

    slot += good_listener
    slot += bad_listener

    with pytest.raises(EventExecutionError) as excinfo:
        slot()
    assert "Error in listener for event 'test_exception'" in excinfo.value.args[0]


@pytest.mark.asyncio
async def test_async_listener_with_propagate_false_propagate_exceptions():

    slot = EventSlot("test_async_exception")
    called = []

    async def good_async_listener():
        await asyncio.sleep(0.01)
        called.append("good_async")

    async def bad_async_listener():
        called.append("bad_async_before")
        await asyncio.sleep(0.01)
        raise ValueError("Async test exception")

    slot += good_async_listener
    slot += bad_async_listener

    with pytest.raises(EventExecutionError) as excinfo:
        await slot.invoke_async()
    assert "Error in listener for event 'test_async_exception'" in excinfo.value.args[0]


def test_listener_with_propagate_false_only_logs(monkeypatch):
    slot = EventSlot("test_no_propagate", propagate_exceptions=False)
    called = []

    mock_logger = Mock()
    monkeypatch.setattr("pynetevents.events.logger", mock_logger)

    def good_listener():
        called.append("good")

    def bad_listener():
        called.append("bad_before")
        raise ValueError("Test exception")

    slot += good_listener
    slot += bad_listener

    # Should not raise despite bad_listener throwing
    slot()

    mock_logger.error.assert_called_once()
    args, _ = mock_logger.error.call_args
    # first arg is the format string, second is event name, third is the exception instance
    assert args[0] == "Error in listener for event '%s': %s"
    assert args[1] == "test_no_propagate"
    assert isinstance(args[2], ValueError)

    assert called == ["good", "bad_before"]


@pytest.mark.asyncio
async def test_async_listener_with_propagate_false_only_logs(monkeypatch):
    slot = EventSlot("test_no_propagate", propagate_exceptions=False)
    called = []

    mock_logger = Mock()
    monkeypatch.setattr("pynetevents.events.logger", mock_logger)

    async def good_listener():
        await asyncio.sleep(0.01)
        called.append("good")

    async def bad_listener():
        called.append("bad_before")
        await asyncio.sleep(0.01)
        raise ValueError("Test exception")

    slot += good_listener
    slot += bad_listener

    # Should not raise despite bad_listener throwing
    await slot.invoke_async()

    mock_logger.error.assert_called_once()
    args, _ = mock_logger.error.call_args
    # first arg is the format string, second is event name, third is the exception instance
    assert args[0] == "Error in listener for event '%s': %s"
    assert args[1] == "test_no_propagate"
    assert isinstance(args[2], ValueError)

    assert called == ["good", "bad_before"]


if __name__ == "__main__":
    pass
