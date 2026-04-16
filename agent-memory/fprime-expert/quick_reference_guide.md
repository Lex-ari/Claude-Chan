---
name: F Prime Quick Reference Guide
description: Fast lookup of critical F Prime framework facts, patterns, and gotchas
type: reference
---

# F Prime Quick Reference Guide

Quick answers to common F Prime framework questions.

## Component Types at a Glance

| Type | Thread | Queue | Async Ports | When to Use |
|------|--------|-------|-------------|-------------|
| Passive | No | No | No | Synchronous processing, no independent work |
| Active | Yes | Yes | Yes (required) | Independent work, long-running tasks |
| Queued | No | Yes | Yes (required) | Queueing without thread (rare) |

**Critical:** Active components MUST have at least one async port. Queued MUST have at least one async AND one sync/guarded.

## Port Kinds Quick Facts

| Kind | Direction | Sync/Async | Thread | Returns | Guarded |
|------|-----------|------------|--------|---------|---------|
| `output` | out | Determined by receiver | Determined by receiver | Maybe | N/A |
| `sync_input` | in | sync | Caller's | Yes | No |
| `async_input` | in | async | Component's | No | No |
| `guarded_input` | in | sync | Caller's | Yes | Yes (component-wide mutex) |

**Critical:** Guarded ports share ONE component-wide mutex. Synchronous call chains run on original caller thread.

## Autocoded Function Patterns

| Pattern | You Do | Example |
|---------|--------|---------|
| `<portName>_handler()` | **IMPLEMENT** | `void schedIn_handler(NATIVE_INT_TYPE portNum, U32 context);` |
| `<portName>_out()` | **CALL** | `this->dataOut_out(0, buffer);` |
| `<mnemonic>_cmdHandler()` | **IMPLEMENT + MUST CALL cmdResponse_out()** | `void START_cmdHandler(FwOpcodeType opCode, U32 cmdSeq);` |
| `tlmWrite_<channel>()` | **CALL** | `this->tlmWrite_Temperature(temp);` |
| `log_<severity>_<event>()` | **CALL** | `this->log_WARNING_HI_TempHigh(temp);` |
| `paramGet_<param>()` | **CALL** | `U32 timeout = this->paramGet_Timeout(valid);` |

**Golden rule:** Pure virtual = IMPLEMENT. Protected method = CALL.

## Command Handler Critical Rule

**MUST** call `cmdResponse_out()` exactly once when command complete:

```cpp
void START_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
    // Do work...
    
    // REQUIRED: Report completion
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}
```

**Forgetting this = command dispatcher hangs waiting for response!**

## Topology Construction Order

**EXACT ORDER REQUIRED:**

1. **Instantiate** all components
2. **Initialize** all components (call `init()`)
3. **Interconnect** ports (get input ports, set output ports)
4. **Register commands** (call `regCommands()` on commanding components)
5. **Load parameters** (call `loadParameters()` on components with parameters)
6. **Start threads** (call `start()` on active components)

**Why strict order:** Each step depends on previous. Violate = crashes or undefined behavior.

## Port Connection Pattern

```cpp
// Get input port from receiving component
Fw::InputCmdPort* inPort = receiver.get_cmdIn_InputPort(0);

// Set output port on sending component
sender.set_cmdOut_OutputPort(0, inPort);
```

**Remember:** Get from INPUT side, set on OUTPUT side.

## Event Severities

| Severity | Use For | Downlinked |
|----------|---------|------------|
| DIAGNOSTIC | Debug messages | Usually no |
| ACTIVITY_LO | Background task info | Yes |
| ACTIVITY_HI | Foreground task info | Yes |
| WARNING_LO | Low severity warnings | Yes |
| WARNING_HI | High severity warnings | Yes |
| FATAL | System must reboot | Yes (triggers response) |
| COMMAND | Command execution trace | Yes |

## Data Types Quick Reference

| Category | Types | Use When |
|----------|-------|----------|
| Integers | U8, U16, U32, U64, I8, I16, I32, I64 | Always (not int/unsigned) |
| Float | F32, F64 | Floating point needs |
| Bool | BOOL | Boolean values |
| String | Fw::StringBase subclasses | Text data |
| Buffer | Fw::Buffer | Large data, memory pools |
| Time | Fw::Time | Timestamps |

**Never use:** `int`, `unsigned`, `long` (size varies by platform)

## Common Gotchas

### 1. Async Port in Passive Component
**Error:** Passive component can't have async_input ports (no queue).
**Fix:** Use sync_input or guarded_input, OR make component active.

### 2. Forgot cmdResponse_out()
**Error:** Command appears to hang, no response.
**Fix:** Always call `cmdResponse_out(opCode, cmdSeq, status)` in command handler.

### 3. Port Not Connected Assert
**Error:** Code asserts when calling output port.
**Fix:** Either connect port in topology OR check `isConnected_<portName>_OutputPort()` before calling.

### 4. Deadlock on Guarded Port
**Error:** Deadlock when guarded port calls back to same component.
**Fix:** Don't create circular call chains with guarded ports. Use async ports to break cycle.

### 5. Wrong Execution Context
**Error:** Unexpected blocking or timing issues.
**Fix:** Understand sync runs on caller thread (blocks), async queues (doesn't block).

### 6. Queue Overflow
**Error:** Active component queue full, messages dropped/blocked.
**Fix:** Increase queue depth in init() OR reduce message rate OR speed up component processing.

### 7. Constructor Port Calls
**Error:** Assert or crash when calling ports in component constructor.
**Fix:** NEVER call ports in constructor. Base class not initialized yet. Use preamble() or handler.

### 8. Parameter Not Loaded
**Error:** paramGet returns PARAM_UNINIT.
**Fix:** Call `loadParameters()` during topology setup after parameter ports connected.

## Memory Management Rules

### Initialization Phase
- **CAN** use `Fw::MemAllocator` / `malloc()` to set up component memory
- Call component `configure()` methods during `configureTopology()`

### Runtime Phase
- **CANNOT** use `malloc()` / `free()` (violates flight software standards)
- **CAN** use `Svc::BufferManager` buffer pools
- Request buffers via `allocate` port, return via `deallocate` port
- Always check `buffer.isValid()` after allocation

## Unit Testing Quick Patterns

```cpp
// Send command
this->sendCmd_START(cmdSeq);
this->component.doDispatch();

// Check command response
ASSERT_CMD_RESPONSE_SIZE(1);
ASSERT_CMD_RESPONSE(0, MyComp::OPCODE_START, cmdSeq, Fw::CmdResponse::OK);

// Check event
ASSERT_EVENTS_SIZE(1);
ASSERT_EVENTS_Started_SIZE(1);

// Check telemetry
ASSERT_TLM_SIZE(1);
ASSERT_TLM_Status(0, expectedStatus);

// Check port invocation
ASSERT_FROM_PORT_HISTORY_SIZE(1);
ASSERT_from_dataOut_SIZE(1);
ASSERT_from_dataOut(0, expectedData);
```

## Sequencing Quick Facts

- **Validation:** CRC + opcode + argument size checked BEFORE execution
- **Execution:** Commands sent one by one to CmdDispatcher
- **Failure:** ANY command failure = sequence ABORTS immediately
- **Timing:** Absolute (UTC) OR relative (seconds delay)
- **Modes:** Auto (full sequence) OR manual (step by step)
- **Blocking:** Enabled = wait for command complete, Disabled = dispatch and continue

## FPP vs C++ Naming

| FPP | C++ Handler | C++ Call |
|-----|-------------|----------|
| `output port dataOut: Fw.Buffer` | N/A (output) | `this->dataOut_out(0, buffer);` |
| `sync input port schedIn: Svc.Sched` | `void schedIn_handler(portNum, context);` | N/A (input) |
| `async command START` | `void START_cmdHandler(opCode, cmdSeq);` | N/A (command) |
| `event Started() severity activity high` | N/A (output) | `this->log_ACTIVITY_HI_Started();` |
| `telemetry Status: U32` | N/A (output) | `this->tlmWrite_Status(status);` |
| `param Timeout: U32` | N/A (input) | `U32 t = this->paramGet_Timeout(valid);` |

## Critical File Locations

| Component | Key Files |
|-----------|-----------|
| Your component | `MyComponent.fpp`, `MyComponent.hpp`, `MyComponent.cpp` |
| Generated base | `build/.../MyComponentComponentBase.hpp`, `...Base.cpp` |
| Test harness | `test/ut/Tester.hpp`, `Tester.cpp` |
| Test base | `build/.../MyComponentTesterBase.hpp`, `...GTestBase.hpp` |
| Topology | `Top/topology.fpp`, `Top/Topology.cpp` |

## When to Use What

| Need | Use |
|------|-----|
| Independent work, own thread | Active component with async ports |
| Simple synchronous processing | Passive component |
| Return value from component | Synchronous get port (sync_input with return) |
| Non-blocking request/response | Callback port pattern (two ports) |
| Thread-safe state access | Guarded input ports |
| Pass large data efficiently | Fw::Buffer with BufferManager |
| Periodic execution | Connect to rate group (schedIn port) |
| Multiple related ports | Parallel port arrays with match/with |
| Cancel long-running work | Synchronous cancel pattern (sync port sets flag) |
| Cross-boundary communication | Hub pattern with serialized ports |

## Help! My Component Won't Compile

**Check:**
1. Did you implement ALL pure virtual functions (handlers)?
2. Did you include both constructors (`#if FW_OBJECT_NAMES`)?
3. Did you add component to CMakeLists.txt SOURCE_FILES?
4. Did you run `fprime-util generate` after changing FPP?
5. Did you call base class constructor in your constructor?

## Help! My Test Won't Pass

**Check:**
1. Did you call `this->component.doDispatch()` after sending async command/port?
2. Did you clear history between tests (`this->clearHistory()`)?
3. Did you set up parameters before component uses them?
4. Did you check array indices in assertions (0-based)?
5. Did your component actually call `cmdResponse_out()`?

## Nomenclature

- **Long form:** "F Prime" (always use in titles, first mention)
- **Short formal:** "F′" (prime symbol, for papers/presentations)
- **Short informal:** "F'" (apostrophe, for code/email)
- **Software token:** "fprime" (all lowercase, for code/repos)
- **Language:** "FPP" or "F Prime Prime" (never "F′′" in writing)
