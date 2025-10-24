"""
Tests for using normal vs weak ref in the EventSlot class in the pynetevents
package and proper reference deletion.
"""

import gc
from typing import List
import asyncio

import pytest

from pynetevents import EventSlot, EventSlotWeakRef

# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=too-few-public-methods


class ListenerA:
    def __init__(self, called: List[str]):
        self.called = called

    def method(self, x):
        self.called.append(("listen_a", x))


class ListenerB:
    def __init__(self, called: List[str]):
        self.called = called

    def method(self, x):
        self.called.append(("listen_b", x))


class ListenerAsync:
    def __init__(self, called: List[str]):
        self.called = called

    async def method(self, x):
        self.called.append(("listen_async", x))
        await asyncio.sleep(0.01)


def test_strong_ref_listener_retained():
    called = []

    listener_a = ListenerA(called)
    listener_b = ListenerB(called)

    slot = EventSlot("test")
    slot_weak = EventSlotWeakRef("test_b")

    slot.subscribe(listener_a.method)
    slot_weak.subscribe(listener_b.method)

    del listener_a
    del listener_b

    gc.collect()

    slot.invoke("hello")
    slot_weak.invoke("hello")

    assert called == [("listen_a", "hello"), ("listen_b", "hello")]


def test_weak_ref_listener_garbage_collected():
    called = []

    listener_a = ListenerA(called)
    listener_b = ListenerB(called)

    slot = EventSlot("test")
    slot_weak = EventSlotWeakRef("test_b")

    slot.subscribe_weak(listener_a.method)
    slot_weak.subscribe_weak(listener_b.method)

    del listener_a
    del listener_b

    gc.collect()

    slot.invoke("hello")
    slot_weak.invoke("hello")

    assert not called


def test_add_calls_weak_on_weak_slot():
    called = []
    listener = ListenerA(called)
    slot = EventSlotWeakRef()

    slot += listener.method

    del listener

    gc.collect()
    slot.invoke("data")

    assert not called


def test_unsub_weak_works():
    called = []
    listener = ListenerA(called)
    slot = EventSlotWeakRef()

    slot.subscribe_weak(listener.method)
    slot.unsubscribe_weak(listener.method)

    slot.invoke("data")

    assert not called


def test_sub_calls_weak_on_weak_slot():
    called = []
    listener = ListenerA(called)
    slot = EventSlotWeakRef()

    slot += listener.method
    slot -= listener.method

    del listener

    gc.collect()
    slot.invoke("data")

    assert not called


def test_unsub_with_weak_removes_not_weak_also():
    called = []
    listener = ListenerA(called)
    slot = EventSlotWeakRef()

    slot += listener.method
    slot.subscribe(listener.method)
    slot -= listener.method

    slot.invoke("data")

    assert not called


@pytest.mark.asyncio
async def test_deleted_weak_ref_listener_gets_silently_removed():
    called = []
    listener = ListenerA(called)
    slot = EventSlotWeakRef()

    slot += listener.method
    del listener
    gc.collect()

    slot("data")

    assert len(slot) == 0

    listener = ListenerA(called)

    slot += listener.method
    del listener
    gc.collect()

    await slot.invoke_async("data")

    assert len(slot) == 0


@pytest.mark.asyncio
async def test_weak_ref_invoke_async_awaits_async():
    called = []
    listener = ListenerAsync(called)
    slot = EventSlotWeakRef()

    slot += listener.method
    await slot.invoke_async("data")
    assert called == [("listen_async", "data")]


if __name__ == "__main__":
    pytest.main("tests/eventslot_ref_test.py")
