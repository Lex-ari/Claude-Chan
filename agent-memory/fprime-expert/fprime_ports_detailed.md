---
name: F Prime Port System Detailed
description: Port design vs instantiation, serialization, special ports, and connection patterns
type: reference
---

# F Prime Port System - Detailed

## Port Design vs Port Instantiation

**Critical distinction:** Port DESIGN (type definition) is separate from port INSTANTIATION (usage in component).

### Port Design (Port Type Definition)
Defines port's **data_type** - the interface signature:
- Name of port type (e.g., `CommandDispatchPort`)
- Arguments transported across port
- Return type (if any)
- NO specification of directionality, sync/async, or guarded behavior

**Location:** Usually in dedicated port directories, separate from components.

**Example FPP:**
```fpp
@ Port returning temperature reading
port GetTemperature() -> F32
```

### Port Instantiation (Port Usage in Component)
Defines port's **kind** - how component uses it:
- Direction: `input` or `output`
- Synchronization: `sync`, `async`, `guarded`
- Array size (if port array)

**Location:** In component .fpp definition.

**Example FPP:**
```fpp
guarded input port getTemp: GetTemperature
```

## Port Characteristics Summary

| Characteristic | Defined In | Examples |
|----------------|-----------|----------|
| **Type (data_type)** | Port design file | CommandDispatchPort, GetTemperature, Sched |
| **Arguments** | Port design file | (U32 cmdId, Fw::CmdStringArg arg) |
| **Return type** | Port design file | `-> F32` or void (default) |
| **Direction** | Component instantiation | `input` or `output` |
| **Kind** | Component instantiation | `sync_input`, `async_input`, `guarded_input` |

## Port Connectivity Rules

1. **Type matching:** Only ports of same type can connect
2. **Direction:** Output ports connect to input ports
3. **Multiple inputs:** Multiple output ports CAN connect to single input port
4. **Single output:** Single output port can connect to ONLY ONE input port at time
5. **Return values:** Only synchronous ports (`sync_input`, `guarded_input`) can return values

## Serialization on Ports

### Normal Typed Ports
Arguments pass directly, no serialization unless crossing serialization boundary.

### When Serialization Occurs
1. Port arguments converted to architecture-independent data buffer
2. Primitives and custom types automatically serialized by framework
3. Serialized buffer passed instead of typed arguments

### Use Cases for Serialization
- Passing data across address spaces (Hub pattern)
- Generic components that don't know data type (command dispatcher, event logger)
- Crossing communication boundaries (network, IPC)

**Critical:** Return values NOT supported with serialization (can't return buffer and get typed response).

## Special Serialized Ports

**Serialized input port:** Accepts serialized buffer from any output port type. Receiving component doesn't unpack automatically.

**Serialized output port:** Can connect to any typed input port. Framework deserializes buffer into typed arguments at receiving end.

**Purpose:** Allows strongly-typed ports to connect through generic "pass-any-data" components.

```
Component A (typed output) 
    → Serialization occurs automatically
        → Generic Hub (serialized ports)
            → Deserialization occurs automatically
                → Component B (typed input)
```

**Why:** Enables reusable C&DH components (CmdDispatcher, EventManager, TlmChan) that work with any data type.

## Port Arrays

Ports can be arrays for managing multiple connections of same type.

**Declaration:**
```fpp
output port cmdOut: [10] Fw.Cmd  // Array of 10 ports
```

**Handler signature:**
```cpp
void cmdOut_handler(NATIVE_INT_TYPE portNum, /* args */);
```

**Invocation:**
```cpp
this->cmdOut_out(3, /* args */);  // Call 4th port in array (0-indexed)
```

**Use case:** Component needs to interact with multiple instances of same port type.

## Port Call Flow for Different Kinds

### Synchronous Port Call
```
Caller thread → output port call 
    → input port (sync_input) 
        → handler executes on caller thread 
            → return to caller
```
Handler runs immediately, blocks caller.

### Guarded Port Call
```
Caller thread → output port call 
    → input port (guarded_input) 
        → LOCK component mutex
            → handler executes on caller thread 
                → UNLOCK component mutex
                    → return to caller
```
Handler runs immediately with mutex protection, blocks caller.

### Asynchronous Port Call
```
Caller thread → output port call 
    → input port (async_input) 
        → serialize args to message 
            → place on component queue 
                → return to caller immediately

[Later, on component thread:]
Component thread → dispatch from queue 
    → deserialize message 
        → handler executes on component thread
```
Handler runs later on component thread, caller not blocked.

## Port Connection Patterns

### One-to-One
Standard: one output → one input

### Many-to-One (Fan-In)
Multiple outputs → single input
- Input handler receives from multiple sources
- Use `portNum` to distinguish source if needed

### Parallel Ports (Correlated Arrays)
Multiple related port arrays on same component, connected to same remote components using same indices.

**Example:** Command dispatcher
- `compCmdSend[i]` sends commands to component i
- `compCmdReg[i]` receives registrations from component i
- Index correlation maintained by topology connections

**FPP enforcement:**
```fpp
match compCmdReg with compCmdSend  // FPP checks parallel wiring
```

## Port Invocation Functions (Autocoded)

### For Input Ports (Handler Implementation)
```cpp
// Pure virtual in generated base, implement in derived class
void portName_handler(
    NATIVE_INT_TYPE portNum,  // 0 if single port, index if port array
    /* port arguments */
);
```

### For Output Ports (Calling Function)
```cpp
// Provided by generated base, call from derived class
this->portName_out(
    NATIVE_INT_TYPE portNum,  // 0 if single port, index if port array
    /* port arguments */
);
```

### Checking Connection Status
```cpp
bool isConnected = this->isConnected_portName_OutputPort(portNum);
if (isConnected) {
    this->portName_out(portNum, args);
}
```

**Why check:** If output port not connected and called, code asserts. Check first if port is optionally connected.

### Getting Port Count
```cpp
NATIVE_INT_TYPE count = this->getNum_portName_InputPorts();
NATIVE_INT_TYPE count = this->getNum_portName_OutputPorts();
```

**Use case:** Scale code to number of ports defined in FPP.

## How to apply

1. **Separate concerns:** Design port type (interface) separately from how components use it (kind)
2. **Match types correctly:** Only connect ports of same type
3. **Choose kind based on needs:**
   - Sync for immediate response, can return values
   - Guarded for thread-safe access to component state
   - Async for decoupled, non-blocking invocation
4. **Consider execution context:** Sync/guarded run on caller thread (watch stack and latency), async runs on component thread
5. **Check connections:** For optional ports, check `isConnected` before calling
6. **Use port arrays:** When component interacts with multiple instances, use arrays and correlate via index
7. **Leverage serialization:** For generic handlers (like command dispatch), serialized ports enable type-agnostic processing
