# pynetevents

A lightweight, flexible **C#-like event system** in Python supporting
**strong/weak references**, **async listeners**, and **exception propagation**.

## Features

- Event slots — attach and fire multiple listeners
- Descriptor-based events
- Supports sync and async listeners
- Weak reference support to avoid memory leaks
- Duplicate listener protection
- Exception propagation
- Clean syntax: `+=` / `-=`

## Table of Contents

- [Quick Start](#quick-start)
- [Event Slots](#eventslots)
- [Event Descriptor](#event-descriptor)
- [Exceptions](#exceptions)

> Check the [API Reference](#api-overview) for full details.

## Quick Start

**Installl**

```bash
pip install pynetevents
```

**Usage**

```python
import asyncio
from pynetevents import Event

class ChatServer:
    on_message = Event()

    def send_message(self, msg):
        self.on_message(msg)

def log(msg):
    print(f"[LOG] {msg}")

async def save(msg):
    await asyncio.sleep(0.1)
    print(f"[ASYNC] Saved {msg}")

server = ChatServer()
server.on_message += log
server.on_message += save
server.send_message("Hello World")
```

## EventSlots

`EventSlot` and `EventSlotWeakRef` are containers for listeners.  
Use `+=` / `-=` to subscribe/unsubscribe.

### EventSlot

Strong references, suitable for long-lived listeners:

```python
from pynetevents import EventSlot

slot = EventSlot("on_data")
slot += lambda x: print(f"Received {x}")
slot("Test")
```

### EventSlotWeakRef

Weak references, automatically cleared when listener is deleted:

```python
from pynetevents import EventSlotWeakRef

class Listener:
    def on_event(self, msg):
        print(msg)

slot = EventSlotWeakRef("on_message")
listener = Listener()
slot += listener.on_event
slot("Hello")
del listener
slot("World")  # No output
```

### Common Usage

- `subscribe`, `subscribe_weak`, `unsubscribe`, `unsubscribe_weak` exist, but
  `+=` / `-=` is simpler.
- `invoke()` calls sync listeners and schedules async (fire-and-forget).
- `invoke_async()` awaits async listeners.

```python
import asyncio
from pynetevents import EventSlot

def sync(msg): print(msg)
async def async_listener(msg): print(msg)

slot = EventSlot("event")
slot += sync
slot += async_listener
slot("Fire-and-forget")
asyncio.run(slot.invoke_async("Awaited"))
```

- Slots can be configured in the constructor:

```python
EventSlot("name", propagate_exceptions=True, allow_duplicate_listeners=True)
```

## Event Descriptor

`Event` is a descriptor to declare class-level events:

```python
from pynetevents import Event

class MyApp:
    on_update = Event(propagate_exceptions=True)
    on_weak = Event(use_weakref_slot=True, allow_duplicate_listeners=True)

app = MyApp()
app.on_update += lambda msg: print(msg)
app.on_update("Update fired")
```

- Automatically creates per-instance slot.
- `+=` / `-=` preferred; direct assignment is restricted.
- Configuration must match if manually assigning a slot in `__init__` as well.

## Exceptions

- **`EventExecutionError`** — Raised when a listener fails.
- **`DuplicateEventListenerError`** — Raised when adding a duplicate listener
  when not allowed.
