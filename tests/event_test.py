# Code under test
# tests/test_eventslot.py
import asyncio
import pytest
from events import EventSlot

@pytest.mark.asyncio
async def test_eventslot_calls_sync_and_async_listeners():
    called = []

    def sync_listener(x):
        called.append(("sync", x))

    async def async_listener(x):
        await asyncio.sleep(0)
        called.append(("async", x))

    slot = EventSlot("test")
    slot += sync_listener
    slot += async_listener

    slot("hello")

    # Give async tasks time to run
    await asyncio.sleep(0.01)

    assert ("sync", "hello") in called
    assert ("async", "hello") in called

def test_eventslot_unsubscribe():
    called = []
    def listener(x): called.append(x)
    slot = EventSlot("test")
    slot += listener
    slot -= listener
    slot("msg")
    assert not called