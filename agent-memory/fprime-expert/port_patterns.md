---
name: F' Port Patterns and Invocation
description: Port types, synchronous vs asynchronous ports, and port invocation patterns
type: feedback
---

# F' Port Patterns and Invocation

Ports are the fundamental communication mechanism in F'. Understanding port patterns is critical for correct component design.

## Port Base Classes (Fw/Port/docs/sdd.md)

### Fw::PortBase
Base class for all ports in F'. Contains:
- Port name
- Port number
- Connection management
- Object registration (if FW_OBJECT_REGISTRATION enabled)

### Fw::InputPortBase / Fw::OutputPortBase
All input and output ports derive from these base classes.

## Port Direction

**Input Port:** Receives port calls (server side)
- Has a handler function in the component
- Can be connected to by one output port

**Output Port:** Makes port calls (client side)
- Invokes connected input port
- Can be connected to multiple input ports (fan-out)

## Port Kinds (Threading Model)

### Synchronous Ports
- Handler executes **on caller's thread**
- Blocking call: caller waits for handler to complete
- Return values allowed
- Can be on any component type (passive, queued, active)

**When to use:**
- Fast operations (< 1ms)
- Return values needed
- Caller and callee have compatible priorities
- No blocking operations (I/O, long computation)

**Example:**
```cpp
// Output port call (caller's thread)
U32 result = this->dataGet_out(portNum, key);

// Input port handler (still on caller's thread)
U32 MyComponent::dataGet_handler(NATIVE_INT_TYPE portNum, U32 key) {
    // Executes on caller's thread
    return computeResult(key);
}
```

### Asynchronous (Async) Ports
- Handler executes **on component's thread** (not caller's thread)
- Non-blocking call: message enqueued, caller returns immediately
- No return values allowed
- Only valid on queued/active components
- Port call serializes arguments into message, enqueues in component's queue

**When to use:**
- Slow operations (file I/O, complex computation)
- Commands, events (must be async in active components)
- Decoupling caller from callee timing
- Preventing priority inversion

**Example:**
```cpp
// Output port call (caller's thread)
this->command_out(portNum, opcode, cmdSeq, args);
// Returns immediately, message enqueued

// Input port handler (component's thread, later)
void MyComponent::command_handler(
    NATIVE_INT_TYPE portNum,
    FwOpcodeType opcode,
    U32 cmdSeq,
    Fw::CmdArgBuffer& args
) {
    // Executes on component's own thread
    // Message was dispatched from queue
}
```

### Guarded Input Ports
- Special synchronous port with mutex protection
- Handler executes on caller's thread BUT protected by mutex
- Ensures thread-safe access to component state
- Available on queued/active components

**When to use:**
- Synchronous access needed (return values)
- Component state must be protected
- Handler is fast but accesses shared state

**Why:** Async ports protect state by serializing access through message queue. Guarded ports protect state via mutex for synchronous calls.

## Port Type Definition Patterns

Ports are defined in FPP:

```fpp
# Synchronous port with return value
port DataGet(key: U32) -> U32

# Asynchronous port, no return
port DataSet(key: U32, value: U32)
```

In component FPP:
```fpp
sync input port dataGetIn: DataGet
async input port dataSetIn: DataSet
output port dataGetOut: DataGet
```

## Port Connection Patterns

### One-to-One
Most common: One output port → One input port

```
ComponentA.dataOut → ComponentB.dataIn
```

### One-to-Many (Fan-out)
One output port → Multiple input ports

```
ComponentA.dataOut → ComponentB.dataIn
ComponentA.dataOut → ComponentC.dataIn
ComponentA.dataOut → ComponentD.dataIn
```

Output port iterates through connections, calls each in sequence.

**Use case:** Broadcasting events, distributing data to multiple consumers

### Many-to-One (Fan-in)
Multiple output ports → One input port

```
ComponentA.dataOut → ComponentD.dataIn
ComponentB.dataOut → ComponentD.dataIn
ComponentC.dataOut → ComponentD.dataIn
```

Input port has `portNum` argument to distinguish callers.

**Use case:** Aggregating data, centralizing command dispatch

## Special Port Types

### Fw::Cmd Port (Commands)
- Always async on component input
- Carries opcode, cmdSeq, argument buffer

### Fw::CmdResponse Port (Command Status)
- Async on dispatcher input
- Reports command completion status

### Fw::Log / Fw::LogText Ports (Events)
- Always async
- Events must not block component execution

### Fw::Tlm Port (Telemetry)
- Synchronous on TlmChan input
- Fast channel update (just stores value)

### Fw::Time Port (Time)
- Synchronous output (returns time)
- Every component has optional time port for timestamps

### Svc::Sched Port (Rate Group)
- Async input for periodic execution
- Carries context value

### Svc::Ping Port (Health Check)
- Async input (must execute on component thread)
- Echoes key back to health component

## Port Handler Method Signatures

Auto-generated handler signatures follow pattern:

**Synchronous with return:**
```cpp
ReturnType portName_handler(
    NATIVE_INT_TYPE portNum,  // Port number (for multiple instances)
    ArgType1 arg1,
    ArgType2 arg2
);
```

**Asynchronous (no return):**
```cpp
void portName_handler(
    NATIVE_INT_TYPE portNum,
    ArgType1 arg1,
    ArgType2 arg2
);
```

**portNum argument:** Distinguishes which port instance called (if component has multiple ports of same type).

## Port Safety Guidelines

**Thread safety:**
- Synchronous ports: Handler executes on caller's thread
  - Must ensure thread-safe access to component state
  - Use guarded ports or manual mutexes if needed
- Asynchronous ports: Handler executes on component's thread
  - State access is automatically serialized via message queue
  - No mutexes needed for component member variables

**Blocking operations:**
- NEVER do blocking operations in synchronous port handlers
  - File I/O, sleeps, waiting on condition variables
  - Blocks caller indefinitely
- Blocking operations OK in async port handlers
  - Only blocks component's own thread

**Priority inversion:**
- Synchronous ports: Low-priority component can block high-priority caller
- Asynchronous ports: Prevent priority inversion (message queued, caller returns)

**Message queue overflow:**
- Async ports enqueue messages
- If queue full, message may be dropped
- Monitor dropped message telemetry
- Size queues appropriately for expected load

**Why these patterns matter:**
- Synchronous = Fast, simple, but coupling and blocking risk
- Asynchronous = Decoupled, non-blocking, but more complex (serialization, queueing)
- Guarded = Thread-safe synchronous access with mutex overhead

**How to apply:**
- Default to async ports for active component inputs (commands, data processing)
- Use sync ports for fast queries with return values
- Use guarded ports when sync access needed but thread safety required
- Never block in sync port handlers
- Document port kind choices in component SDD
- Test with multiple threads to verify thread safety
