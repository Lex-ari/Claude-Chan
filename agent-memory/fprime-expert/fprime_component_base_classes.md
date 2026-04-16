---
name: F Prime Component Base Classes and Component Types
description: Hierarchy and behavior of PassiveComponentBase, QueuedComponentBase, and ActiveComponentBase
type: reference
---

# F Prime Component Base Classes

## Component Type Hierarchy

```
PassiveComponentBase (Fw/Comp/PassiveComponentBase.hpp)
    └── QueuedComponentBase (Fw/Comp/QueuedComponentBase.hpp)
            └── ActiveComponentBase (Fw/Comp/ActiveComponentBase.hpp)
```

## PassiveComponentBase
**Location:** `Fw/Comp/PassiveComponentBase.hpp`

**Purpose:** Base class for all F Prime components

**Key Members:**
- `m_idBase` - ID base for opcodes, event IDs, channel IDs
- `m_instance` - Component instance number

**Key Methods:**
- `setIdBase(FwIdType)` - Set the component ID base
- `getIdBase()` - Get the component ID base
- `getInstance()` - Get component instance number
- `init(FwEnumStoreType instance)` - Initialize component

**Threading:** No threading - methods execute on caller's thread

**Port Handlers:** Execute synchronously on caller's thread

## QueuedComponentBase
**Location:** `Fw/Comp/QueuedComponentBase.hpp`

**Purpose:** Adds message queue to PassiveComponentBase

**Key Members:**
- `Os::Queue m_queue` - Message queue for asynchronous port calls
- `m_msgsDropped` - Counter for dropped messages

**Key Methods:**
- `createQueue(FwSizeType depth, FwSizeType msgSize)` - Create message queue
- `deinit()` - Allows de-initialization on teardown
- `doDispatch()` - Pure virtual method to dispatch a single message (implemented by autocoder)
- `getNumMsgsDropped()` - Return number of messages dropped
- `incNumMsgDropped()` - Increment dropped message count

**Threading:** No thread yet, but has queue infrastructure

**MsgDispatchStatus enum:**
- `MSG_DISPATCH_OK` - Dispatch was normal
- `MSG_DISPATCH_EMPTY` - No more messages in queue
- `MSG_DISPATCH_ERROR` - Error dispatching messages
- `MSG_DISPATCH_EXIT` - Message requesting loop exit

## ActiveComponentBase
**Location:** `Fw/Comp/ActiveComponentBase.hpp`

**Purpose:** Adds task/thread to QueuedComponentBase

**Key Members:**
- `Os::Task m_task` - Task object for active component
- `m_stage` - Lifecycle stage (CREATED, DISPATCHING, FINALIZING, DONE)

**Key Methods:**
- `start(priority, stackSize, cpuAffinity, identifier)` - Start component task
- `exit()` - Exit task in active component
- `join()` - Join the thread (wait for completion)
- `preamble()` - Virtual method called before event loop (can be overridden)
- `dispatch()` - Dispatch a single message from queue
- `finalizer()` - Virtual method called after exiting loop (can be overridden)

**Threading:** Has its own thread that dispatches messages from queue

**Lifecycle Stages:**
1. **CREATED** - Initial stage, call preamble
2. **DISPATCHING** - Component is dispatching messages
3. **FINALIZING** - Penultimate stage, call finalizer
4. **DONE** - Done, doing nothing

**Task State Machine:**
- `s_taskStateMachine()` - Task lifecycle state machine (static)
- `s_taskLoop()` - Standard multi-threading task loop (static)

## FPP Component Keywords Map to Base Classes

- **`passive component`** → Inherits from PassiveComponentBase
- **`queued component`** → Inherits from QueuedComponentBase
- **`active component`** → Inherits from ActiveComponentBase

## Port Handler Execution Context

### Passive Components
- All port handlers execute on **caller's thread**
- No queuing, no serialization
- Must be thread-safe if called from multiple threads

### Queued/Active Components
- **Async ports** → Messages queued, handler executes on component's thread
- **Sync ports** → Handler executes on **caller's thread** (not queued)
- **Guarded ports** → Handler protected by mutex, executes on caller's thread

## Why This Matters

The component base class determines:
1. **Threading model** - Where handlers execute
2. **Serialization** - Whether operations are serialized via queue
3. **Performance characteristics** - Synchronous vs asynchronous behavior
4. **Error handling** - Queue overflow possibilities for active components

**How to apply:** When analyzing component behavior, always check:
1. Is it passive, queued, or active? (Look at FPP definition)
2. Are the ports async, sync, or guarded?
3. This determines which thread executes each handler
