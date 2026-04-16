---
name: F' Component Types and Threading Model
description: Passive, queued, and active components with threading and lifecycle details
type: feedback
---

# F' Component Types and Threading Model

F' has three fundamental component types based on threading behavior:

## Component Type Hierarchy

```
Fw::ObjBase (root of all F' objects)
  └── Fw::PassiveComponentBase
        └── Fw::QueuedComponentBase
              └── Fw::ActiveComponentBase
```

## 1. Passive Components (PassiveComponentBase)

**Characteristics:**
- No thread or message queue
- All port handlers execute **on the caller's thread**
- Synchronous execution only
- Lightest weight component type

**When to use:**
- Simple data transformations
- Stateless operations
- Components that don't need asynchronous behavior

**Files:** `Fw/Comp/PassiveComponentBase.hpp`

## 2. Queued Components (QueuedComponentBase)

**Characteristics:**
- Has a message queue (`Os::Queue m_queue`)
- No dedicated thread (borrows caller's thread for dispatch)
- Can have async input ports (messages enqueued)
- Tracks dropped messages (`m_msgsDropped`)

**Key method:** `doDispatch()` - pure virtual, must be implemented to dispatch one message

**When to use:**
- Rarely used directly; typically use Active components instead
- Special cases where queue is needed without a dedicated thread

**Files:** `Fw/Comp/QueuedComponentBase.hpp`

## 3. Active Components (ActiveComponentBase)

**Characteristics:**
- Has a message queue (inherited from QueuedComponentBase)
- Has a dedicated thread (`Os::Task m_task`)
- Async port handlers enqueue messages; thread dispatches them
- Most common component type for flight software

**Threading lifecycle:**
1. **start()** - Creates and starts the task thread
2. **preamble()** - Called once before message loop (override for initialization)
3. **dispatch()** - Message dispatch loop (calls doDispatch() repeatedly)
4. **finalizer()** - Called once after message loop exits (override for cleanup)
5. **exit()** - Signals component to exit message loop
6. **join()** - Waits for thread to complete

**Lifecycle stages (enum Lifecycle):**
- CREATED - Initial stage, call preamble
- DISPATCHING - Component is dispatching messages
- FINALIZING - Penultimate stage, call finalizer
- DONE - Finished, doing nothing

**When to use:**
- Components that process commands, events, or telemetry
- Any component needing asynchronous behavior
- Components with significant processing workload

**Why:** Active components with dedicated threads enable concurrent execution, prevent blocking, and allow prioritization. The message queue decouples producers from consumers.

**How to apply:**
- Default to active components for most flight software
- Use passive components only for simple, stateless utilities
- Always implement preamble() and finalizer() for initialization/cleanup
- Ensure thread-safe access to component state (protected by message dispatch)

**Files:** `Fw/Comp/ActiveComponentBase.hpp`, `Fw/Comp/ActiveComponentBase.cpp`

## Port Handler Threading Rules

**Synchronous ports:** Always execute on caller's thread (regardless of component type)

**Asynchronous ports:**
- Passive component: Not allowed
- Queued/Active component: Enqueue message, execute on component's thread

This threading model is **critical** for understanding component behavior and preventing race conditions.
