"""
Tests for the Event Descriptor use in classes.
"""

import time
import pytest
from pynetevents import Event


class MyService:
    test_event = Event()


def test_event_as_class_attribute():
    holder = MyService()
    holder2 = MyService()
    called = []

    def listener(x):
        called.append(x)
        print(f"Listener A called with {x}")

    def listener_b(x):
        called.append(x)
        print(f"Listener B called with {x}")

    holder.test_event += listener
    holder2.test_event += listener_b

    holder2.test_event("data")
    time.sleep(4)
    holder.test_event("data")


def test_event_assignment_raises():
    holder = MyService()

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
    test_event_as_class_attribute()
