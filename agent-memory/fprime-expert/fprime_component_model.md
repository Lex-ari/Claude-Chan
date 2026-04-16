---
name: F Prime Component Model
description: Component types, threading model, queue behavior, port kinds, and execution contexts
type: reference
---

# F Prime Component Model

## Component Types

F Prime has three component types, each with different threading and queuing capabilities.

### Passive Component
- **Has thread**: No
- **Has queue**: No
- **Execution context**: Supplied by invoking component
- **Supported port kinds**: `sync_input`, `guarded_input`, `output`
- **Cannot use**: `async_input` ports

**When to use:** Simple stateless or synchronous processing, no independent work

### Active Component
- **Has thread**: Yes
- **Has queue**: Yes
- **Execution context**: Own thread for async work, invoker thread for sync/guarded
- **Supported port kinds**: All (`sync_input`, `guarded_input`, `async_input`, `output`)
- **Must have**: At least one `async_input` port (otherwise effectively passive with unused thread)

**When to use:** Independent processing, long-running work, need to decouple from caller

**Critical behavior:**
- Thread dispatches messages from queue automatically
- Synchronous and guarded ports still run on invoker's thread (not queued)
- Queue depth must be specified during `init()`

### Queued Component
- **Has thread**: No
- **Has queue**: Yes
- **Execution context**: Supplied by invoker for synchronous dispatch
- **Supported port kinds**: All three kinds
- **Must have**: At least one `sync_input` or `guarded_input` to unload queue, and at least one `async_input`

**When to use:** Rarely. Need queueing without dedicated thread, external dispatcher controls timing.

**Critical behavior:**
- User must implement synchronous port to manually unload/dispatch queue
- Asynchronous ports place messages on queue, but don't auto-dispatch
- If no sync port unloads queue, messages accumulate and never process

## Component Class Hierarchy

Each component has three implementation layers:

1. **Core Framework Class**: Base class from framework (`ActiveComponentBase`, `PassiveComponentBase`, `QueuedComponentBase`)
2. **Generated Component-Specific Base**: Autocoded class inheriting from core, provides all framework feature implementations
3. **Developer Implementation Class**: User-written class inheriting from generated base, implements handlers

```
Fw::PassiveComponentBase (framework)
    ↓
MyComponentComponentBase (autocoded from .fpp)
    ↓
MyComponent (developer implementation)
```

## Port Kinds and Component Compatibility

### Port Kinds (from component perspective)

| Port Kind | Direction | Sync/Async | Guarded | May Return Data | Thread Context |
|-----------|-----------|------------|---------|-----------------|----------------|
| `output` | out | — | — | — | Determined by receiving port |
| `sync_input` | in | synchronous | no | yes | Invoker's thread |
| `async_input` | in | asynchronous | no | no | Component's thread (queued) |
| `guarded_input` | in | synchronous | yes | yes | Invoker's thread, mutex-protected |

**Note:** Guarded ports must be synchronous (by definition). Mutex is component-wide.

### Component Type to Port Kind Compatibility

| Component Type | Can Use output | Can Use sync/guarded | Can Use async | Notes |
|----------------|----------------|----------------------|---------------|-------|
| Passive | Yes (0+) | Yes (0+) | No | No queue to support async |
| Active | Yes (0+) | Yes (0+) | Yes (1+) | Need at least one async or thread is wasted |
| Queued | Yes (0+) | Yes (1+) | Yes (1+) | Need sync to unload queue manually |

## Execution Context Critical Understanding

**Synchronous port invocation:** Runs on caller's thread. Fast, direct, but blocks caller.

**Guarded port invocation:** Runs on caller's thread but locks component-wide mutex first. Blocks caller AND prevents concurrent guarded port invocations on same component.

**Asynchronous port invocation:** Message placed on component queue, caller returns immediately. Component thread dispatches from queue later. Cannot return values.

**Output port invocation:** Execution context determined by receiving component's port kind. If receiver has sync_input, runs on caller's thread. If receiver has async_input, queued at receiver.

## Component Initialization Sequence

1. **Constructor**: DO NOT make port calls. Base class not initialized yet. Set up member variables only.

2. **init()**: Call on all components after instantiation, before interconnection.
   - For queued/active: Must provide queue depth
   - Optional: instance ID if component instanced multiple times
   - Can call from derived class init() wrapper

3. **Interconnection**: Connect ports using get/set port functions (see topology construction)

4. **regCommands()**: For commanding components, register commands with dispatcher

5. **loadParameters()**: For components with parameters, load from PrmDb

6. **start()**: For active components only, start the thread
   - Arguments: identifier (unique ID), priority (0-255), stackSize
   - Starts thread which calls `preamble()`, then enters message loop, then `finalizer()`

### Active Component Lifecycle Hooks

**preamble()**: Virtual function called once on component thread before message loop starts. Use for one-time thread-specific initialization.

**finalizer()**: Virtual function called once on component thread after message loop exits. Use for cleanup.

Both run on component's thread, both optional (virtual with empty default implementations).

## Reentrancy and Thread Safety Concerns

**Guarded ports deadlock risk:** If Component A with guarded port calls Component B, and B calls back to A's guarded port before returning, deadlock occurs (trying to lock already-held mutex).

**Synchronous port call chains:** If A calls B synchronously, and B calls C synchronously, all run on A's original thread. Be aware of stack depth and execution time.

**Component-wide mutex:** All guarded ports on a component share ONE mutex. Concurrent calls to different guarded ports still serialize.

**Active component queue overflow:** If messages arrive faster than component thread processes them, queue fills. Behavior depends on queue overflow configuration (drop, block, or assert).

## How to apply

When designing component:
1. Determine if needs independent work (thread) or if can run on caller thread
2. If thread needed, use active component with async_input ports
3. If just need synchronous processing, use passive component
4. Queued component rarely needed - consider active instead
5. For thread-safe state access, use guarded_input ports (automatically mutex-protected)
6. Be mindful of execution context: sync/guarded run on caller thread, async runs on component thread
7. Size queue depth based on expected message rate and processing speed (active components)
