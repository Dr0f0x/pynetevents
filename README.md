# pynetevents

[![CI](https://github.com/Dr0f0x/pynetevents/actions/workflows/python-ci.yml/badge.svg)](https://github.com/Dr0f0x/pynetevents/actions/workflows/python-ci.yml)
[![Publish](https://github.com/Dr0f0x/pynetevents/actions/workflows/publish.yml/badge.svg)](https://github.com/Dr0f0x/pynetevents/actions/workflows/publish.yml)

A lightweight, flexible implementation of a **C#-like event system** in Python
that provides simple, composable event slots — with support for both **strong**
**and weak references**, **async listeners**, and **exception propagation**.

## Features

- Event slots — attach and fire multiple listeners easily
- Descriptor-based events that restrict outside access to the event
- Supports async and sync listeners
- Possibility to use weak reference listeners to avoid memory leaks
- Duplicate listener protection (if wanted)
- Exception propagation for listener failures
- Clean syntax: `+=` to subscribe, `-=` to unsubscribe

## Table of Contents

- [Quick Start](#quick-start)
- [Event Slots](#eventslots)
  - [EventSlot](#eventslot)
  - [EventSlotWeakRef](#eventslotweakref)
  - [Common Usage](#common-usage)
- [Event Descriptor](#event-descriptor)
- [Exceptions](#exceptions)

> For a full overview of all classes, methods, and options, check out the
> [API Reference](#api-ovettrvriew).

## Quick Start

#### Installation

```bash
pip install pynetevents
```

#### Usage

```python
import asyncio
from pynetevents import Event

class ChatServer:
    on_message = Event()

    def send_message(self, message):
        self.on_message(message)

def log_message(msg):
    print(f"[LOG] Received: {msg}")

async def save_message(msg):
    await asyncio.sleep(0.1)
    print(f"[ASYNC] Saved message: {msg}")

server = ChatServer()
server.on_message += log_message
server.on_message += save_message

server.send_message("Hello, world!")
```

## EventSlots

EventSlots are the centerpiece of this implementation. Essentially they are
Containers that hold all registered listeners and allow to invoke each of them
centrally and easily add/remove said listeners.

There are two EventSlots provided by the package:

### EventSlot

The **standard event slot** (`EventSlot`) keeps **strong references** to all
listeners.  
This means that as long as the slot exists, all listeners will remain in memory
(and possibly the class they are a method of) — even if nothing else references
them.

This is ideal for most scenarios where listeners are meant to persist for the
lifetime of an object or system (e.g., global events, core application signals).

```python
from pynetevents import EventSlot

# Create a new event slot
slot = EventSlot("on_data")

def printer(data):
    print(f"Printer received: {data}")

async def saver(data):
    print(f"[ASYNC] Saved data: {data}")

# Subscribe listeners
slot += printer
slot += saver

# Fire synchronously — runs sync listeners immediately
slot("Hello, strong world!")

# Fire asynchronously — awaits async listeners
import asyncio
asyncio.run(slot.invoke_async("Async invocation example"))

# Remove a listener
slot -= printer

slot("Goodbye!")  # Only saver runs (if invoked asynchronously)
```

### EventSlotWeakRef

The **weak reference event slot** (`EventSlotWeakRef`) is designed to **avoid
memory leaks** by holding listeners via **weak references** whenever possible.
When a listener (typically a bound method) goes out of scope or its owning
object is deleted, it is **automatically removed** from the slot — no manual
unsubscription required.

This makes it ideal for **instance-based event systems** where many temporary
objects may register callbacks.

```python
from pynetevents import EventSlotWeakRef

class Listener:
    def __init__(self, name):
        self.name = name

    def on_event(self, msg):
        print(f"{self.name} received: {msg}")

# Create the weakref slot
slot = EventSlotWeakRef("on_message")

# Create and register a listener
listener = Listener("Alpha")
slot += listener.on_event

# Fire event
slot("Hello!")  # -> Alpha received: Hello!

# Delete the listener instance
del listener

# The weak reference has been cleared automatically
slot("World!")  # -> No output (listener no longer exists)
```

### Common Usage

Both of these classes have the inherited methods `subscribe`,`subscribe_weak`,
`unsubscribe`, `unsubscribe_weak` that come from their common base class which
in theory makes it possible to subscribe using a weakref to the normal
`EventSlot`, although i would recommend aganst doing so, as it is bound to be
very confusing.

Instead the easier way would be to use the overloaded `+=` and `-=` operators,
like the examples above do, that are overriden for these classes. For an
`EventSlot` instance they use the `subscribe` and `unsubscribe` methods under
the hood and for the `EventSlotWeakRef` the according alternatives.

Invoking all the listeners of a slot (= Invoking the event can be done) by using
the `Invoke` or `InvokeAsync` methods. The difference being that the first calls
synchronous listeners normally and only schedules async ones (fire and forget),
while the async version actually awaits them.

```python
import asyncio
from pynetevents import EventSlot, EventSlotWeakRef

def sync_listener(msg):
    print(f"[SYNC] Received: {msg}")

async def async_listener(msg):
    await asyncio.sleep(0.1)
    print(f"[ASYNC] Processed: {msg}")

slot = EventSlot("on_event")

slot += sync_listener
slot += async_listener

# Fire synchronously (does NOT await async listeners)
slot("Fire-and-forget example")

# Fire asynchronously (awaits async listeners properly)
asyncio.run(slot.invoke_async("Awaited example"))
```

An `EventSlot` can be invoked with any kind of arguments that will be properly
forwarded to all the listeners (which of course must be able to accept them). As
a short cut for calling the sync invoke method one can also call the EventSlot
itself, which will do the exact same.

```python
from pynetevents import EventSlot

def on_data_received(data, status):
    print(f"Received '{data}' with status: {status}")

# Create an EventSlot
slot = EventSlot("on_data")
slot += on_data_received

# You can invoke with any arguments the listeners expect
slot.invoke("Sample payload", status=200)

# Shortcut: calling the slot directly does the same as invoke()
slot("Another payload", status=404)
```

`EventSlots` can be configured in their behaviour by using the constructor
arguments. You can customize whether you want exceptions to be propagated or
only logged and wether you want to allow duplicate_listeners or throw an
exception like the default.

```python
from pynetevents import EventSlot

# Default behavior:
# - Exceptions are caught and logged (not propagated)
# - Duplicate listeners are not allowed
default_slot = EventSlot("default_slot")

# Exceptions are propagated (raised to the caller)
propagating_slot = EventSlot("propagating_slot", propagate_exceptions=True)

# Duplicate listeners are allowed
duplicates_allowed_slot = EventSlot("duplicates_allowed_slot", allow_duplicate_listeners=True)

# Both customized: exceptions propagated AND duplicates allowed
custom_slot = EventSlot(
    "custom_slot",
    propagate_exceptions=True,
    allow_duplicate_listeners=True
)
```

## Event Descriptor

In addition to the `Slot` classes the package offers a custom descriptor for
declaring `EventSlots` as class attributes, that restricts access to the
attribute and allows for some other benefits. This decriptor is simply called
`Event` as I would recommend it as the main way of declaring and using this
event implementation.

```python
from pynetevents import Event

# Example class using Event descriptor
class ChatServer:
    # Declare events as class attributes
    on_message = Event()

# Example listeners
def log_message(msg):
    print(f"[LOG] Message received: {msg}")

server = ChatServer()

# Subscribe listeners normally using '+='
# the EventSlot instance is automatically created here and uses the name of the attribute `on_message`
server.on_message += log_message

# Fire event
server.on_message("Hello World!")

# Would throw an error as it assigns a new instance
server.on_message = EventSlot()
```

The `__get__` method will automatically create an `EventSlot` for each instance
if one does not already exist. And if one does it checks that the configuration
of the existing object and the descriptor fit. Internally created slots are
stored inside the instance dict just like a normal attribute would

The `__set__` method only allows assigning the same `EventSlot` instance to
itself (altough the instance itself can be changed), this prohibits assigning
new objects to the attribute and is intended to encourage using the `+=` and
`-=` operators.

The `__set_name` method gets the name of the `Event` attribute and uses it for
the created `EventSlots`.

The `Event` provides the same configuration options as the `EventSlots`
(propagate_excpetions, allow_duplicate_listeners) and additionally one to choose
wether created instances should be `EventSlotWeakRef` or normal ones.

```python
from pynetevents import Event

class MyApp:
    # Normal EventSlot, exceptions propagated
    on_update = Event(propagate_exceptions=True)

    # Weak reference EventSlot, duplicate listeners allowed
    on_weak_update = Event(
        use_weakref_slot=True,
        allow_duplicate_listeners=True
    )

    # Normal EventSlot with all defaults
    on_default = Event()
```

If you prefer you can still create the `EventSlot` instance in the `__init__`
method of the class and it will be used by the descriptor, however the
configurations must match (or not be passed in the constructor of the slot
object). Basically, if the descriptor wants to use a **weak reference slot**
(`EventSlotWeakRef`) but the found instance is a **normal `EventSlot`**, or if
any configuration parameter like `propagate_exceptions` or
`allow_duplicate_listeners` does not match, the descriptor will **raise an
error**.

```python
from pynetevents import Event, EventSlot, EventSlotWeakRef

class MyApp:
    on_update = Event(use_weakref_slot=True, propagate_exceptions=True)
    on_call = Event(propagate_exceptions=False)

    def __init__(self):
        # You can provide your own EventSlot instance
        # Must match the descriptor configuration (type and params)
        self.on_update = EventSlotWeakRef(
            "on_update",
            propagate_exceptions=True
        )

        # Or do not provide the concering arguments (= leave defaults)
        self.on_call = EventSlot()
```

## Exceptions

`pynetevents` provides two very verbose exception types to handle event-related
errors:

- **`EventExecutionError`**  
  Raised when a listener throws an exception during event invocation.  
  This allows you to catch and inspect errors from individual listeners while
  optionally continuing to run other listeners.

- **`DuplicateEventListenerError`**  
  Raised when attempting to add the same listener multiple times to an
  `EventSlot` if `allow_duplicate_listeners` is set to `False`.  
  This prevents accidental duplicate registrations and ensures predictable event
  behavior.
