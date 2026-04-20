---
name: FPP and F Prime Framework Integration
description: How FPP integrates with F Prime framework including special ports, framework types, component lifecycle, and FSW patterns
type: reference
originSessionId: c7708e45-a599-4300-a457-572b467a90ee
---
# FPP and F Prime Framework Integration

## Framework Overview

FPP is the modeling language for F Prime (F´), a component-based flight software framework. FPP generates C++ code that integrates with the F Prime framework.

## Framework Dependencies

FPP assumes F Prime framework provides certain built-in definitions:

### Framework Types
- `FwSizeStoreType`: Type for storing string lengths in serialization
- `FwSizeType`: Size type
- `FwOpcodeType`: Command opcode type  
- `FwIndexType`: Array index type

### Framework Constants
- `FW_FIXED_LENGTH_STRING_SIZE`: Default maximum string length (when `string size N` not specified)

### Framework Ports
Standard F Prime ports used by components:
- `Fw.Cmd`: Command port
- `Fw.CmdReg`: Command registration port
- `Fw.CmdResponse`: Command response port
- `Fw.Log`: Event (log) port
- `Fw.LogText`: Text event port
- `Fw.Time`: Time port
- `Fw.Tlm`: Telemetry port
- `Fw.PrmGet`: Parameter get port
- `Fw.PrmSet`: Parameter set port
- `Fw.Buffer`: Buffer port
- `Fw.Com`: Communication buffer port

### Framework Modules
Build dependencies based on component features:
- `Fw_Comp`: Required for passive components
- `Fw_CompQueued`: Required for queued or active components
- `Os`: Required for active/queued components or guarded ports (needs OS primitives)

## Component Lifecycle

### Generated vs. Hand-Written Code

**FPP generates:**
- Base component class (e.g., `ComponentAc.hpp/cpp`)
- Port connection interfaces
- Command dispatcher skeleton
- Event/telemetry emission methods
- Serialization/deserialization

**Developer provides:**
- Derived component implementation
- Port handler implementations  
- Command handler implementations
- Business logic

**Example:**
```cpp
// Generated: MyComponentAc.hpp
class MyComponentAc : public ComponentBase { ... };

// Hand-written: MyComponent.hpp
class MyComponent : public MyComponentAc {
  void cmdHandler_COMMAND_NAME(FwOpcodeType opCode, U32 cmdSeq, Args...);
  void portHandler_INPUT_PORT(Args...);
};
```

## Component Kinds and Threading

### Active Components
**FPP:** `active component ComponentName { ... }`

**Behavior:**
- Has own thread
- Has message queue
- Processes async commands and ports on queue
- Requires `queue size` and optionally `stack size`, `priority`, `cpu` in instance definition

**Framework integration:**
- Thread created during component initialization
- Messages dispatched from queue by framework
- Component handlers run in component's thread context

### Queued Components
**FPP:** `queued component ComponentName { ... }`

**Behavior:**
- Has message queue but no dedicated thread
- External thread (e.g., rate group) dispatches messages
- Lighter weight than active components

**Framework integration:**
- `run()` method called by external scheduler
- Processes one or more queued messages per call

### Passive Components
**FPP:** `passive component ComponentName { ... }`

**Behavior:**
- No queue, no thread
- Synchronous calls only
- Handlers run in caller's thread context

**Framework integration:**
- Direct function calls, no message passing

## Port Mechanisms

### Port Types and Invocation

**Synchronous ports (`sync`):**
- Direct function call
- Caller blocks until return
- Can have return value
- Handler runs in caller's thread

**Asynchronous ports (`async`):**
- Message queued
- Caller returns immediately  
- Handler runs in component's thread (active) or when dispatched (queued)
- Cannot have return value

**Guarded ports (`guarded`):**
- Synchronous with mutex protection
- Thread-safe for shared resources
- Requires OS module

### Port Directionality

**Input ports:**
- Component provides handler implementation
- Other components invoke the port
- Generated signature: `void portHandler_PortName(Args...)`

**Output ports:**
- Component invokes the port
- Connected to another component's input port
- Generated method: `void portName_out(PortNumber, Args...)`

### Special Ports

Special ports have predefined semantics in F Prime:

**Command Ports:**
```fpp
command recv port cmdIn      # Receives commands
command reg port cmdRegOut   # Registers commands with dispatcher
command resp port cmdRespOut # Sends command responses
```

**Event Ports:**
```fpp
event port eventOut          # Emits events
text event port textEventOut # Emits text events
time get port timeGetOut     # Gets timestamps for events
```

**Telemetry Ports:**
```fpp
telemetry port tlmOut        # Emits telemetry
time get port timeGetOut     # Gets timestamps for telemetry
```

**Parameter Ports:**
```fpp
param get port prmGetOut     # Gets parameter values
param set port prmSetOut     # Sets parameter values
# Also requires command ports
```

**Data Product Ports:**
```fpp
product send port productSendOut   # Sends data products
product get port productGetOut     # Gets buffers (pull model)
# OR
product request port productRequestOut  # Requests buffers (push model)
product recv port productRecvIn         # Receives requests (push model)
time get port timeGetOut           # Gets timestamps
```

### Port Number Arrays

**FPP definition:**
```fpp
output port cmdOut: [10] Fw.Cmd
```

**Usage in C++:**
```cpp
// Invoke specific port number
this->cmdOut_out(0, opcode, seq, args);
this->cmdOut_out(5, opcode, seq, args);
```

**Connections:** Each array element connects independently
```fpp
dispatcher.cmdOut[0] -> receiver1.cmdIn
dispatcher.cmdOut[1] -> receiver2.cmdIn
```

## Command Handling

### Command Flow in F Prime

1. Ground/sequencer sends command to dispatcher
2. Dispatcher looks up registered handler
3. Dispatcher invokes component's command port
4. Command queued (async) or called directly (sync)
5. Component processes command in handler
6. Component sends response via command response port

### Command Kinds

**Sync commands:**
- Execute immediately in dispatcher's context
- Block command flow until complete
- Use for fast, non-blocking operations

**Async commands:**
- Queued to component
- Allow command flow to continue
- Use for operations requiring time or blocking

**Guarded commands:**
- Sync with mutex protection
- Thread-safe execution

### Generated Command Handler

**FPP:**
```fpp
async command SET_MODE(
    mode: U8 @< Operating mode
) opcode 0x10
```

**Generated signature:**
```cpp
void SET_MODE_cmdHandler(
    FwOpcodeType opCode,
    U32 cmdSeq,
    U8 mode
);
```

**Implementation responsibilities:**
- Execute command logic
- Send command response (success/failure)

**Command response:**
```cpp
this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
```

## Event Reporting

### Event Flow
1. Component invokes event port method
2. Framework adds timestamp (via time get port)
3. Event routed to event logger
4. Event sent to ground system

### Event Severity Levels
- `ACTIVITY_HI` / `ACTIVITY_LO`: Normal operational events
- `COMMAND`: Command-related events
- `DIAGNOSTIC`: Debug/diagnostic information
- `FATAL`: Fatal errors requiring safing
- `WARNING_HI` / `WARNING_LO`: Warning conditions

### Generated Event Methods

**FPP:**
```fpp
event THRESHOLD_EXCEEDED(
    value: F32
) severity warning high format "Threshold exceeded: {}"
```

**Generated method:**
```cpp
void log_WARNING_HI_THRESHOLD_EXCEEDED(F32 value);
```

**Usage in implementation:**
```cpp
this->log_WARNING_HI_THRESHOLD_EXCEEDED(measuredValue);
```

### Event Throttling

**FPP:**
```fpp
event NOISY_EVENT(x: U32) \
  severity diagnostic \
  format "Value: {}" \
  throttle 10 every { seconds = 60 }
```

**Framework behavior:**
- Emits first 10 instances
- Suppresses further instances for 60 seconds
- Automatically resets after timeout
- Can manually reset via generated method

## Telemetry Channels

### Telemetry Flow
1. Component updates telemetry channel
2. Framework adds timestamp
3. Telemetry routed to telemetry database
4. Telemetry packetized and downlinked

### Update Modes

**Always:** Emit every update
```fpp
telemetry Counter: U32 update always
```

**On Change:** Emit only when value changes
```fpp
telemetry Mode: U8 update on change
```

### Generated Telemetry Methods

**FPP:**
```fpp
telemetry Temperature: F32 id 0x20
```

**Generated method:**
```cpp
void tlmWrite_Temperature(F32 value);
```

**Usage:**
```cpp
this->tlmWrite_Temperature(currentTemp);
```

### Telemetry Limits

**FPP defines limits for ground monitoring:**
```fpp
telemetry Pressure: F32 \
  low { red 0.5, orange 0.7, yellow 0.9 } \
  high { yellow 5.1, orange 5.5, red 6.0 }
```

Ground system alerts when value crosses thresholds.

## Parameters

### Parameter Flow
1. Ground system sends parameter updates via commands
2. Framework stores parameters persistently
3. Component retrieves parameters via parameter get port
4. Component uses parameters in logic

### Generated Parameter Methods

**FPP:**
```fpp
param UPDATE_RATE: F32 default 1.0
```

**Generated method:**
```cpp
F32 paramGet_UPDATE_RATE();
```

**Usage:**
```cpp
F32 rate = this->paramGet_UPDATE_RATE();
```

**Parameter updates:**
- Handled automatically by framework
- Component notified via `parameterUpdated` callback

## Topologies

### Topology Structure in F Prime

**Topology defines:**
- Component instances and their configuration
- Port connections between instances
- Connection patterns (commands, events, telemetry)
- Initialization order

### Generated Topology Code

**FPP:**
```fpp
topology MainTopology {
  instance dispatcher: Svc.CommandDispatcher base id 0x100
  instance receiver: App.Receiver base id 0x200
  
  connections Commanding {
    dispatcher.cmdOut[0] -> receiver.cmdIn
  }
}
```

**Generated:**
- Topology setup functions
- Instance declarations
- Connection setup code
- Initialization sequence

### Connection Patterns

**Command pattern:** Auto-connects command ports
```fpp
connections C {
  command
}
```
Generates connections: cmdIn → dispatcher, dispatcher → cmdOut, etc.

**Event pattern:** Auto-connects event ports
```fpp
connections C {
  event
}
```

**Other patterns:** `telemetry`, `param`, `health`, `time`, `text event`

### Base IDs and ID Ranges

**Base ID:** Starting value for component's dictionary IDs

**ID computation:** `actualID = baseID + relativeID`

**Example:**
```fpp
instance comp: MyComponent base id 0x100

# In MyComponent:
event ERROR id 0x05  # Actual ID: 0x105
telemetry COUNT id 0x10  # Actual ID: 0x110
```

**Constraint:** Component ID ranges cannot overlap

## State Machines

### State Machine Integration

**External state machines:**
```fpp
state machine DeviceDriver  # Implemented by hand
```

**Internal state machines:**
```fpp
state machine Controller {
  signal Start
  signal Stop
  initial enter IDLE
  state IDLE { on Start enter RUNNING }
  state RUNNING { on Stop enter IDLE }
}
```
Framework generates state machine implementation.

### State Machine in Components

**FPP:**
```fpp
active component Manager {
  state machine instance device: DeviceDriver
}
```

**Framework integration:**
- Signals become async port invocations
- State machine runs in component's thread
- Generated methods to send signals

## Serialization

### Automatic Serialization

Framework provides serialization for all FPP types:
- Primitive types: Direct binary serialization
- Enums: As underlying integer type
- Arrays: Sequential element serialization
- Structs: Sequential member serialization
- Strings: Length prefix + characters

### Wire Format

Standard F Prime binary format:
- Big-endian for multi-byte values
- Size prefix for variable-length data
- Compact representation

### Usage in Generated Code

Serialization methods auto-generated for:
- Port parameters
- Command arguments
- Event parameters
- Telemetry values
- Struct/array types

## Ground System Integration

### Dictionary Generation

**Tool:** `fpp-to-dict`

**Output:** JSON/XML dictionary containing:
- All commands with opcodes and parameters
- All events with IDs, severities, and formats
- All telemetry channels with IDs and types
- All parameters with IDs and defaults

**Ground system uses dictionary to:**
- Encode commands
- Decode telemetry and events
- Display values with correct types and formats

### Format Strings

**FPP format strings map to ground display:**
```fpp
event VALUE_CHANGED(
    name: string
    value: F32
) format "Parameter {} changed to {.2f}"
```

Ground system substitutes parameters into format string for display.
