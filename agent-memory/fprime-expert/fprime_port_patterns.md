---
name: F Prime Port Invocation Patterns and Semantics
description: Port types (sync/async/guarded), execution contexts, serialization behavior, and port handler patterns
type: reference
---

# F Prime Port Invocation Patterns

## Port Direction

### Input Ports
- Declared on receiving component
- Implement handler methods
- Can be sync, async, or guarded

### Output Ports
- Declared on sending component
- Call methods on connected input ports
- No port type qualifier (determined by connected input)

## Port Type Qualifiers (Input Ports)

### Synchronous (sync)
**Declaration:** `sync input port portName: PortType`

**Execution:** Runs on **caller's thread** (no queuing)

**Blocking:** Yes - caller blocks until handler completes

**Use Cases:**
- Fast operations that must complete immediately
- Operations that return values
- Caller needs result before proceeding

**Example:** `Svc::Health.Run` port
```fpp
sync input port Run: Svc.Sched
```

**Handler Execution:**
```
Caller Thread → Output Port Call → Input Port Handler (on caller thread) → Return
```

### Asynchronous (async)
**Declaration:** `async input port portName: PortType`

**Execution:** Runs on **component's thread** (queued)

**Blocking:** No - caller returns immediately after queuing

**Use Cases:**
- Long-running operations
- Operations that should not block caller
- Active/queued components processing messages

**Example:** `Svc::ActiveRateGroup.CycleIn`
```fpp
async input port CycleIn: Svc.Cycle
```

**Handler Execution:**
```
Caller Thread → Output Port Call → Queue Message → Return
                                        ↓
Component Thread → Dequeue → Input Port Handler (on component thread)
```

### Guarded
**Declaration:** `guarded input port portName: PortType`

**Execution:** Runs on **caller's thread** with **mutex protection**

**Blocking:** Yes - caller blocks while handler executes under mutex

**Use Cases:**
- Thread-safe access to shared state
- Passive components called from multiple threads
- Critical sections that need atomicity

**Example:** `Svc::TlmChan.TlmRecv`
```fpp
guarded input port TlmRecv: Fw.Tlm
```

**Handler Execution:**
```
Caller Thread → Output Port Call → Lock Mutex → Input Port Handler → Unlock Mutex → Return
```

## Port Execution Context Summary

| Port Type | Thread | Queued | Mutex | Blocking | Component Type |
|-----------|--------|--------|-------|----------|----------------|
| sync | Caller | No | No | Yes | Any |
| async | Component | Yes | No | No | Active/Queued |
| guarded | Caller | No | Yes | Yes | Any (typically Passive) |

## Port Handler Naming Convention

**Auto-Generated Handler Name:**
```
<portName>_handler(FwIndexType portNum, <port arguments>)
```

**Examples:**
```cpp
void CycleIn_handler(FwIndexType portNum, Os::RawTime& cycleStart);
void TlmRecv_handler(FwIndexType portNum, FwChanIdType id, Fw::Time& timeTag, Fw::TlmBuffer& val);
void Run_handler(FwIndexType portNum, U32 context);
```

**Port Number:** First argument is always port index (for multi-port arrays)

## Port Arrays

**Declaration:**
```fpp
output port PingSend: [10] Svc.Ping
async input port PingReturn: [10] Svc.Ping
```

**Invocation:**
```cpp
// Call specific port instance
this->PingSend_out(portIndex, key);
```

**Handler:**
```cpp
// Receive from any port instance
void PingReturn_handler(FwIndexType portNum, U32 key) {
    // portNum tells which instance was called
}
```

**Port Matching:**
```fpp
match PingSend with PingReturn
```
- Enforces port array sizes match
- Port index correspondence (e.g., PingSend[0] ↔ PingReturn[0])

## Pre/Post Message Hooks (Async Ports)

### Pre-Message Hook
**Signature:** `<portName>_preMsgHook(FwIndexType portNum, <port arguments>)`

**Execution:** Runs on **caller's thread** BEFORE message queued

**Use Case:** Set flags or perform quick checks before queuing

**Example:** `ActiveRateGroup.CycleIn_preMsgHook()`
```cpp
void CycleIn_preMsgHook(FwIndexType portNum, Os::RawTime& cycleStart) {
    // Runs on caller thread, before message queued
    this->m_cycleStarted = true;  // Detect cycle slip
}
```

### Post-Message Hook
**Signature:** `<portName>_postMsgHook(FwIndexType portNum, <port arguments>)`

**Execution:** Runs on **caller's thread** AFTER message queued

**Use Case:** Cleanup or post-queue actions on caller thread

## Port Connection Checking

**Methods:**
```cpp
bool isConnected_<portName>_OutputPort(FwIndexType portNum);
FwIndexType getNum_<portName>_OutputPorts();
```

**Usage:**
```cpp
if (this->isConnected_PingSend_OutputPort(port)) {
    this->PingSend_out(port, key);
}
```

**Why Check:** Avoid calling unconnected ports (causes assertion)

## Special Port Types (Autocoder Generated)

### Command Ports
```fpp
command recv port CmdDisp
command reg port CmdReg
command resp port CmdStatus
```

**Purpose:** Framework command handling

**Auto-Generated Methods:**
- `cmdResponse_out(opCode, cmdSeq, response)` - Send command status
- `regCommands()` - Register component's commands with dispatcher

### Event Ports
```fpp
event port Log
text event port LogText
```

**Purpose:** Event/log emission

**Auto-Generated Methods:**
- `log_<SEVERITY>_<EventName>(<args>)` - Emit specific event

### Telemetry Ports
```fpp
telemetry port Tlm
```

**Purpose:** Telemetry channel updates

**Auto-Generated Methods:**
- `tlmWrite_<ChannelName>(value)` - Write telemetry channel

### Time Port
```fpp
time get port Time
```

**Purpose:** Get current time for timestamps

**Auto-Generated Methods:**
- `getTime()` - Returns `Fw::Time`

### Parameter Ports
```fpp
param get port PrmGet
param set port PrmSet
```

**Purpose:** Parameter load/update

**Auto-Generated Methods:**
- `paramGet_<ParamName>(val)` - Get parameter value
- `paramSet_<ParamName>(val)` - Set parameter value

## Port Serialization

**Mechanism:** Port arguments are serialized when crossing component boundaries

**Serializable Types:**
- Primitive types (U32, F32, etc.)
- Enums
- Arrays
- Strings
- User-defined serializable types

**Port Definition:**
```fpp
port MyPort(
    arg1: U32
    arg2: F32
    arg3: string size 40
)
```

**Auto-Generated:** Serialization/deserialization code

## Port Hook Declaration (FPP)

**Async with hook:**
```fpp
async input port seqCmdBuff: [N] Fw.Com hook
```

**Hook Method:** `<portName>_overflowHook(portNum, <port arguments>)`

**Trigger:** Message queue full, can't queue message

**Example:** `CmdDispatcher.seqCmdBuff_overflowHook()`
```cpp
void seqCmdBuff_overflowHook(FwIndexType portNum, Fw::ComBuffer& data, U32 context) {
    // Called when queue overflow occurs
    // Extract opcode and log warning
}
```

**Use Case:** DOS protection, graceful degradation

## Port Drop Semantic

**Declaration:**
```fpp
async input port CycleIn: Svc.Cycle drop
```

**Behavior:** If queue full, message is **dropped** (not queued, no hook called)

**Use Case:** Rate group cycles where missing a cycle is acceptable

**Alternative:** `hook` - Call hook instead of dropping

## Critical Design Patterns

### 1. Sync for Fast, Must-Complete Operations
- Rate group `Run` ports (must complete before next cycle)
- Health `Run` port (quick health checks)
- Parameter `getPrm` (synchronous load)

### 2. Async for Decoupled, Long Operations
- Command buffers (`seqCmdBuff`)
- Command responses (`cmdResponseIn`)
- Ping returns (`PingReturn`)

### 3. Guarded for Shared State Protection
- Telemetry updates (`TlmRecv`)
- Parameter updates (`setPrm`)
- Buffer allocation (`bufferGetCallee`)

### 4. Pre-Message Hooks for Immediate Actions
- ActiveRateGroup cycle slip detection
- Time-critical flag setting

### 5. Overflow Hooks for Graceful Degradation
- CommandDispatcher queue overflow handling
- Drop events instead of blocking

### 6. Port Matching for Symmetry
- Health: `PingSend` matches `PingReturn`
- CmdDispatcher: `compCmdSend` matches `compCmdReg`
- Ensures port array sizes correspond

### 7. Connection Checking Before Invocation
- Avoid assertions on unconnected ports
- Allows optional ports (e.g., status ports)

## Common Pitfalls

### 1. Calling Unconnected Output Ports
- **Problem:** Assertion failure
- **Solution:** Check `isConnected_<portName>_OutputPort()`

### 2. Sync Port Deadlock
- **Problem:** Sync port handler calls back to caller
- **Solution:** Use async or guarded ports for callback paths

### 3. Guarded Port Performance
- **Problem:** Mutex contention on high-rate calls
- **Solution:** Minimize handler work, consider double-buffering

### 4. Async Queue Overflow
- **Problem:** Queue fills up under high load
- **Solution:** Use hook, drop semantic, or back-pressure mechanism

### 5. Pre-Hook Blocking
- **Problem:** Pre-hook blocks caller (defeats async benefit)
- **Solution:** Keep pre-hooks minimal (flag setting only)

**How to apply:** When defining component ports:
1. Choose sync for fast, must-complete operations
2. Choose async for decoupled, long operations (active components)
3. Choose guarded for shared state protection (passive components)
4. Consider overflow hooks for async ports on critical paths
5. Always check port connection before calling output ports
6. Match port arrays where correspondence is required
