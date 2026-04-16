---
name: F Prime Component Lifecycle and Autocoding System
description: Component creation workflow, autocoder generated code, initialization sequence, and lifecycle management
type: reference
---

# F Prime Component Lifecycle and Autocoding System

## Component Development Workflow

### 1. Create Component Skeleton
```bash
fprime-util new --component
```

**Generates:**
- `ComponentName.fpp` - FPP interface definition
- `ComponentName.hpp` - C++ header (implementation)
- `ComponentName.cpp` - C++ source (implementation)
- `CMakeLists.txt` - Build configuration

### 2. Define Interface in FPP
**Edit:** `ComponentName.fpp`

**Define:**
- Component type (passive/queued/active)
- Ports (input/output)
- Commands
- Events
- Telemetry channels
- Parameters

### 3. Generate Autocoded Files
```bash
fprime-util impl
```

**Generates/Updates:**
- `ComponentNameComponentAc.hpp` - Autocoded base class header
- `ComponentNameComponentAc.cpp` - Autocoded base class implementation

**Updates:**
- `ComponentName.hpp` - Adds handler stubs if needed
- `ComponentName.cpp` - Adds handler stubs if needed

### 4. Implement Handler Logic
**Edit:** `ComponentName.cpp`

**Implement:**
- Port handlers
- Command handlers
- Optional parameter callbacks

### 5. Add to Topology
**Edit topology files:**
- `instances.fpp` - Instantiate component
- `topology.fpp` - Connect ports

### 6. Build and Test
```bash
fprime-util build
fprime-util check  # Run unit tests
```

## Autocoded Component Structure

### Inheritance Hierarchy
```
Fw::PassiveComponentBase (or QueuedComponentBase/ActiveComponentBase)
    ↓
ComponentNameComponentBase (autocoded)
    ↓
ComponentName (user implementation)
```

### ComponentBase (Autocoded) Responsibilities

**Port Management:**
- Port registration and connection
- Port invocation methods (`<portName>_out()`)
- Port connection checking (`isConnected_<portName>_OutputPort()`)
- Port handler dispatch

**Command Management:**
- Command registration (`regCommands()`)
- Command dispatch to handler
- Command response sending (`cmdResponse_out()`)

**Event Management:**
- Event emission methods (`log_<SEVERITY>_<EventName>()`)
- Event serialization and port invocation

**Telemetry Management:**
- Telemetry write methods (`tlmWrite_<ChannelName>()`)
- Telemetry serialization and port invocation

**Parameter Management:**
- Parameter get/set methods (`paramGet_<ParamName>()`, `paramSet_<ParamName>()`)
- Parameter load orchestration
- Parameter callbacks (`parameterUpdated()`, `parametersLoaded()`)

**Time Management:**
- Time get method (`getTime()`)

### User Implementation Responsibilities

**Handler Implementation:**
- Port handlers (e.g., `schedIn_handler()`)
- Command handlers (e.g., `CMD_NO_OP_cmdHandler()`)
- Optional parameter callbacks

**State Management:**
- Component-specific state variables
- Initialization logic
- Cleanup logic

**Business Logic:**
- Algorithm implementation
- Data processing
- External interface integration

## Component Initialization Sequence

### 1. Construction Phase
```cpp
ComponentName comp("instanceName");
```

**Actions:**
- Call base class constructor
- Initialize user member variables
- No port connections yet

### 2. Init Phase
```cpp
comp.init(instanceNumber);
```

**Actions:**
- Set instance number
- Set ID base (opcode base, event ID base, channel ID base)
- Initialize component infrastructure

**Order:** All components constructed, then all initialized

### 3. Port Connection Phase
```cpp
// In topology
comp1.outputPort → comp2.inputPort
```

**Actions:**
- Wire output ports to input ports
- Build inter-component communication graph

### 4. Command Registration Phase
```cpp
comp.regCommands();
```

**Actions:**
- Call `compCmdReg` port for each command
- Register opcodes with CommandDispatcher
- Happens after port connections complete

### 5. Parameter Load Phase
```cpp
// Ground command
prmDb.PRM_LOAD_FILE
comp.LOAD_PARAMETERS
```

**Actions:**
- PrmDb loads parameter file
- Each component requests its parameters
- `parametersLoaded()` callback invoked

### 6. Task Start Phase (Active Components)
```cpp
comp.start(priority, stackSize);
```

**Actions:**
- Create OS task/thread
- Call `preamble()` virtual method
- Enter message dispatch loop

**Order:** Start after all initialization complete

## Component Lifecycle States

### Active Component States

**CREATED:**
- Component constructed and initialized
- Ports connected
- Task not started

**PREAMBLE:**
- Task started
- `preamble()` virtual method executing
- Not yet dispatching messages

**DISPATCHING:**
- Normal operation
- Dispatching messages from queue
- Processing port invocations, commands

**FINALIZING:**
- Shutdown initiated
- `finalizer()` virtual method executing
- Cleaning up before exit

**DONE:**
- Task exited
- Component shut down

## Autocoded Method Naming Conventions

### Output Port Invocation
```cpp
void <portName>_out(FwIndexType portNum, <port arguments>);
```

**Example:**
```cpp
this->schedOut_out(0, context);
```

### Input Port Handler
```cpp
void <portName>_handler(FwIndexType portNum, <port arguments>);
```

**Example:**
```cpp
void schedIn_handler(FwIndexType portNum, U32 context) override;
```

### Command Handler
```cpp
void <CMD_NAME>_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, <arguments>);
```

**Example:**
```cpp
void CMD_NO_OP_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) override;
```

### Event Emission
```cpp
void log_<SEVERITY>_<EventName>(<event arguments>);
```

**Example:**
```cpp
this->log_ACTIVITY_HI_ModeChanged(newMode);
```

### Telemetry Write
```cpp
void tlmWrite_<ChannelName>(<channel type> value);
```

**Example:**
```cpp
this->tlmWrite_Temperature(currentTemp);
```

### Parameter Get/Set
```cpp
Fw::ParamValid paramGet_<ParamName>(<param type>& value);
void paramSet_<ParamName>(<param type> value);
```

**Example:**
```cpp
F32 gainValue;
if (this->paramGet_Gain(gainValue) == Fw::ParamValid::VALID) {
    // Use gainValue
}
```

## ID Base Management

**Purpose:** Prevents ID collisions across components

**ID Types:**
- Opcode base - Command opcodes
- Event ID base - Event IDs
- Channel ID base - Telemetry channel IDs

**Calculation:** Typically based on component instance number

**Configuration:** Set during topology initialization

**Example:**
```cpp
comp.setIdBase(0x0100);  // All IDs offset by 0x0100
```

## Virtual Methods (Can Override)

### Active Components

**preamble():**
- Called before message dispatch loop starts
- Runs on component's thread
- Use for thread-specific initialization

**finalizer():**
- Called after message dispatch loop exits
- Runs on component's thread
- Use for cleanup

### Parameter Callbacks

**parameterUpdated(FwPrmIdType id):**
- Called when single parameter updated
- Use for parameter-specific actions

**parametersLoaded():**
- Called after all parameters loaded
- Use for initialization requiring all parameters

## Component Types and Threading

### Passive Component
- **Thread:** Caller's thread
- **Queue:** None
- **Use Case:** Stateless utilities, simple data transformations
- **Example:** Type converters, math libraries

### Queued Component
- **Thread:** No dedicated thread
- **Queue:** Has message queue
- **Use Case:** Serialized access without dedicated thread (rare)
- **Example:** Specialized use cases

### Active Component
- **Thread:** Dedicated thread
- **Queue:** Message queue
- **Use Case:** Asynchronous processing, long operations
- **Example:** CmdDispatcher, ActiveRateGroup, TlmChan

## Port Handler Execution Context

**Passive Component:**
- All handlers run on caller's thread
- No serialization (must be thread-safe)

**Queued Component:**
- Async handlers run on caller's thread (queued for later)
- Sync handlers run on caller's thread (immediate)
- Guarded handlers run on caller's thread (mutex protected)

**Active Component:**
- Async handlers run on component's thread (queued)
- Sync handlers run on caller's thread (immediate)
- Guarded handlers run on caller's thread (mutex protected)

## FPP Autocoder Triggers

**Regenerate autocoded files when:**
1. Add/remove/modify ports
2. Add/remove/modify commands
3. Add/remove/modify events
4. Add/remove/modify telemetry channels
5. Add/remove/modify parameters
6. Change component type (passive/queued/active)

**Command:**
```bash
fprime-util impl
```

**Warning:** Autocoder preserves user implementation but updates base class

## Build System Integration

**CMakeLists.txt Structure:**
```cmake
set(SOURCE_FILES
  ComponentName.fpp
  ComponentName.cpp
)

register_fprime_module()
```

**Dependencies:**
- Framework libraries (Fw::*)
- Port type libraries
- Custom type libraries

**Build from repo root:**
```bash
fprime-util build
```

## Component Testing

**Unit Test Structure:**
```
ComponentName/
  test/
    ut/
      ComponentNameTester.hpp
      ComponentNameTester.cpp
      ComponentNameTestMain.cpp
```

**Generated by:**
```bash
fprime-util new --component
```

**Run tests:**
```bash
cd ComponentName
fprime-util check
```

## Critical Best Practices

1. **Always regenerate after FPP changes:** Run `fprime-util impl`
2. **Don't modify autocoded files:** Changes will be overwritten
3. **Initialize member variables:** Constructor or init() method
4. **Send command responses:** Every command handler must call `cmdResponse_out()`
5. **Check port connections:** Use `isConnected_` before output calls
6. **Thread-safe state access:** Use mutexes or guarded ports for passive components
7. **Keep handlers efficient:** Especially sync and guarded handlers
8. **Emit events for significant actions:** Aids debugging and operations
9. **Update telemetry regularly:** Typically in rate group handlers
10. **Load parameters at startup:** Call `LOAD_PARAMETERS` command after PrmDb loads

**How to apply:** When creating new component:
1. Start with clear FPP definition of interface
2. Run `fprime-util impl` to generate base class
3. Implement handlers in user class
4. Add to topology and wire ports
5. Build, test, iterate
6. Never modify autocoded files
