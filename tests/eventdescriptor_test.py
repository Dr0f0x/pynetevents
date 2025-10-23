"""
Tests for the Event Descriptor use in classes.
"""

import pytest
from pynetevents import Event, EventSlot

# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=too-few-public-methods


class EventService:
    test_event = Event()


class EventServiceWithOnlyDescriptor:
    test_event = Event(propagate_exceptions=False, allow_duplicate_listeners=True)


class EventServiceWithConfiguredSlot:
    test_event = Event()

    def __init__(self):
        self.test_event = EventSlot(
            propagate_exceptions=False, allow_duplicate_listeners=True
        )


class EventServiceWithConfiguredDescriptor:
    test_event = Event(propagate_exceptions=False, allow_duplicate_listeners=True)

    def __init__(self):
        self.test_event = EventSlot()


class EventServiceWithConfiguredDescriptorAndSlot:
    test_event = Event(propagate_exceptions=False, allow_duplicate_listeners=True)

    def __init__(self):
        self.test_event = EventSlot(
            propagate_exceptions=False, allow_duplicate_listeners=True
        )


class EventServiceNamed:
    test_event = Event("event_named")


class EventServiceWithDifferentName:
    test_event = Event()

    def __init__(self):
        self.test_event = EventSlot("different_name")


class EventServiceWithDifferentPropagate:
    test_event = Event(propagate_exceptions=True)

    def __init__(self):
        self.test_event = EventSlot(propagate_exceptions=False)


class EventServiceWithDifferentDuplicateListeners:
    test_event = Event(allow_duplicate_listeners=True)

    def __init__(self):
        self.test_event = EventSlot(allow_duplicate_listeners=False)


class EventServiceWithDifferentTypeOnName:
    test_event = Event()

    def __init__(self):
        self.test_event = object()


def test_event_without_passed_name_uses_attribute_name():
    holder = EventService()
    assert holder.test_event.name == "test_event"


def test_event_with_passed_name_uses_passed_name():
    holder = EventService()
    assert holder.test_event.name == "test_event"


PARAMETER_CONSISTENCY_ERR_MSG = "has inconsistent parameters"


def test_different_name_slot_and_descriptor_throws_exception():
    with pytest.raises(AttributeError) as excinfo:
        holder = EventServiceWithDifferentName()
        holder.test_event += lambda: None
    assert PARAMETER_CONSISTENCY_ERR_MSG in str(excinfo.value)


def test_different_params_slot_and_descriptor_throws_exception():
    with pytest.raises(AttributeError) as excinfo:
        holder = EventServiceWithDifferentDuplicateListeners()
        holder.test_event += lambda: None
    assert PARAMETER_CONSISTENCY_ERR_MSG in str(excinfo.value)

    with pytest.raises(AttributeError) as excinfo:
        holder = EventServiceWithDifferentPropagate()
        holder.test_event += lambda: None
    assert PARAMETER_CONSISTENCY_ERR_MSG in str(excinfo.value)


def test_different_type_on_name_throws_exception():
    with pytest.raises(TypeError) as excinfo:
        holder = EventServiceWithDifferentTypeOnName()
        holder.test_event += lambda: None
    assert "Tried to assign a non-EventSlot value to event attribute" in str(
        excinfo.value
    )


def test_configured_slot_in_init():
    holder = EventServiceWithConfiguredSlot()
    assert holder.test_event.propagate_exceptions is False
    assert holder.test_event.allow_duplicate_listeners is True


def test_configured_descriptor_with_slot_present():
    holder = EventServiceWithConfiguredDescriptor()
    assert holder.test_event.propagate_exceptions is False
    assert holder.test_event.allow_duplicate_listeners is True


def test_only_configured_descriptor_present():
    holder = EventServiceWithOnlyDescriptor()
    assert holder.test_event.propagate_exceptions is False
    assert holder.test_event.allow_duplicate_listeners is True


def test_configured_descriptor_and_slot():
    holder = EventServiceWithConfiguredDescriptorAndSlot()
    assert holder.test_event.propagate_exceptions is False
    assert holder.test_event.allow_duplicate_listeners is True


def test_event_separation_between_class_instances():
    holder_a = EventService()
    holder_b = EventService()
    called = []

    def listener_a(x):
        called.append(x)

    def listener_b(x):
        called.append(x)

    holder_a.test_event += listener_a
    holder_b.test_event += listener_b

    holder_b.test_event("data b")
    assert called == ["data b"]
    called.clear()
    holder_a.test_event("data a")
    assert called == ["data a"]


def test_event_assignment_raises():
    holder = EventService()

    # += should work
    called = []

    def listener(x):
        called.append(x)

    holder.test_event += listener
    holder.test_event("test")
    assert called == ["test"]

    # Using '=' should raise AttributeError
    with pytest.raises(AttributeError) as excinfo:
        holder.test_event = None
    assert "can only be modified via '+=' or '-='" in str(excinfo.value)


if __name__ == "__main__":
    pass
