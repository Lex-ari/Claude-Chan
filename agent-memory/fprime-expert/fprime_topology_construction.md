---
name: F Prime Topology Construction
description: Component instantiation, initialization, interconnection, command registration, and startup sequence
type: reference
---

# F Prime Topology Construction

Complete sequence for building an F Prime application from components.

## Step 1: Instantiate Components

Components can be instantiated using any C++ memory model:
- Static allocation
- Heap allocation (`new`)
- Stack allocation (rare for components)

**Constructor requirements:**
- If `FW_OBJECT_NAMES` enabled: Constructor takes name string
- If `FW_OBJECT_NAMES` disabled: No-argument constructor
- Must define BOTH constructors (use `#if FW_OBJECT_NAMES`)

**Critical:** DO NOT make port calls in constructor. Base class not initialized yet.

**Example:**
```cpp
#if FW_OBJECT_NAMES
MyComponent myComp("MyComponent");
#else
MyComponent myComp;
#endif
```

## Step 2: Initialize Components

Call `init()` on every component after instantiation, before interconnection.

**Function signature:**
```cpp
// For passive components:
void init(NATIVE_INT_TYPE instance = 0);

// For queued/active components:
void init(NATIVE_INT_TYPE queueDepth, NATIVE_INT_TYPE instance = 0);
```

**Parameters:**
- `queueDepth`: Message queue size (active/queued only). Size based on message rate and processing speed.
- `instance`: Optional instance ID if component instantiated multiple times in topology

**Why before interconnection:** Init prepares component's port infrastructure.

**Example:**
```cpp
passiveComp.init(0);
activeComp.init(10, 0);  // Queue depth of 10 messages
```

## Step 3: Interconnect Components

Connect output ports to input ports using get/set port pointer functions.

### Interface Port Connection

**Get input port pointer:**
```cpp
<PortType>* get_<portName>_InputPort(NATIVE_INT_TYPE portNum);
```

**Set output port pointer:**
```cpp
void set_<portName>_OutputPort(
    NATIVE_INT_TYPE portNum,
    <PortType>* port
);
```

**Example:**
```cpp
// Connect componentA's output to componentB's input
Fw::InputCmdPort* inPort = componentB.get_cmdIn_InputPort(0);
componentA.set_cmdOut_OutputPort(0, inPort);
```

### Standard Port Connection Patterns

**Command ports:**
```cpp
// Get command dispatch input port
Fw::InputCmdPort* cmdPort = component.get_CmdDisp_InputPort();
dispatcher.set_compCmdSend_OutputPort(index, cmdPort);

// Set command status output port
Fw::InputCmdResponsePort* statusPort = dispatcher.get_compCmdStat_InputPort(index);
component.set_CmdStatus_OutputPort(statusPort);

// Set command registration output port
Fw::InputCmdRegPort* regPort = dispatcher.get_compCmdReg_InputPort(index);
component.set_CmdReg_OutputPort(regPort);
```

**Telemetry ports:**
```cpp
Fw::InputTlmPort* tlmPort = tlmChan.get_TlmRecv_InputPort();
component.set_Tlm_OutputPort(tlmPort);

Fw::InputTimePort* timePort = timeSource.get_timeGetPort_InputPort();
component.set_Time_OutputPort(timePort);
```

**Event logging ports:**
```cpp
Fw::InputLogPort* logPort = eventManager.get_LogRecv_InputPort();
component.set_Log_OutputPort(logPort);

Fw::InputLogTextPort* textPort = textLogger.get_TextLogger_InputPort();
component.set_TextLog_OutputPort(textPort);

// Time port shared with telemetry
component.set_Time_OutputPort(timePort);
```

**Parameter ports:**
```cpp
Fw::InputPrmGetPort* getPort = prmDb.get_getPrm_InputPort();
component.set_ParamGet_OutputPort(getPort);

Fw::InputPrmSetPort* setPort = prmDb.get_setPrm_InputPort();
component.set_ParamSet_OutputPort(setPort);
```

### Serialized Port Connection

For serialized ports (Hub pattern):
```cpp
// Typed port to serialized port
Fw::InputSerializePort* serPort = hub.get_portIn_InputPort(0);
component.set_typedPortOut_OutputPort(0, serPort);
```

## Step 4: Register Commands

For each component with commands, call `regCommands()` to register opcodes with dispatcher.

**Pattern:**
```cpp
component.regCommands();
```

**What happens:**
- Component calls registration port for each defined command
- Dispatcher stores opcode-to-component mapping
- Must happen after command ports connected

**When:** After interconnection, before starting active components.

## Step 5: Load Parameters

For components with parameters, call `loadParameters()` to retrieve initial values from PrmDb.

**Pattern:**
```cpp
component.loadParameters();
```

**What happens:**
- Component requests each parameter via getPrm port
- PrmDb returns value (or default if not found)
- Values cached in component base class
- Available via `paramGet_<paramName>()` calls

**When:** After parameter ports connected, after PrmDb loaded file.

**Can be called again:** To reload parameters if PrmDb updated at runtime.

## Step 6: Start Active Components

Start threads for active components last, after all setup complete.

**Function signature:**
```cpp
bool start(
    NATIVE_INT_TYPE identifier,  // Unique thread ID
    NATIVE_INT_TYPE priority,    // 0 = low, 255 = high
    NATIVE_INT_TYPE stackSize,   // Stack size in bytes
    NATIVE_INT_TYPE cpuAffinity = -1  // Optional: pin to CPU core
);
```

**Returns:** true on success, false on failure

**Example:**
```cpp
activeComp.start(
    1,        // Unique identifier
    100,      // Priority
    10*1024,  // 10KB stack
    -1        // Let OS choose core
);
```

**What happens:**
1. OS creates thread
2. Thread calls `preamble()` virtual function (once, on component thread)
3. Thread enters message dispatch loop
4. Processes async port calls and async commands from queue
5. On exit, calls `finalizer()` virtual function (once, on component thread)

**Important:** Start in priority order if thread priorities matter. Higher priority threads should start first to ensure proper preemption behavior.

## Complete Topology Construction Sequence

```cpp
// 1. Instantiate all components
ComponentA compA("CompA");
ComponentB compB("CompB");
CmdDispatcher cmdDisp("CmdDisp");
// ... etc

// 2. Initialize all components
compA.init(10, 0);  // Active with queue depth 10
compB.init(0);      // Passive
cmdDisp.init(20, 0);
// ... etc

// 3. Interconnect all ports
// Connect A to B
compA.set_dataOut_OutputPort(0, compB.get_dataIn_InputPort(0));
// Connect command infrastructure
compA.set_CmdReg_OutputPort(cmdDisp.get_compCmdReg_InputPort(0));
compA.set_CmdStatus_OutputPort(cmdDisp.get_compCmdStat_InputPort(0));
cmdDisp.set_compCmdSend_OutputPort(0, compA.get_CmdDisp_InputPort());
// ... etc

// 4. Register commands
compA.regCommands();
compB.regCommands();
// ... etc

// 5. Load parameters
compA.loadParameters();
compB.loadParameters();
// ... etc

// 6. Start active components (priority order)
compA.start(1, 100, 10*1024);   // Highest priority
cmdDisp.start(2, 90, 10*1024);  // Lower priority
// ... etc
```

## Topology in FPP

Modern F Prime uses FPP to define topology declaratively.

**Component instances:**
```fpp
instance myComp: MyComponent base id 0x100
```

**Port connections:**
```fpp
connections MyTopology {
    compA.dataOut -> compB.dataIn
    compB.statusOut -> compA.statusIn
}
```

**Autocoded:**
- FPP generates topology header with instance declarations
- FPP generates topology.cpp with port connection code
- Developer fills in instance creation and initialization in topology setup functions

## Shutdown Sequence

For active components, call `exit()` on component base class to gracefully stop thread:

```cpp
activeComp.exit();  // Signals thread to exit message loop
// Thread calls finalizer(), then terminates
```

## Common Topology Patterns

### Rate Group Driven Components
```cpp
// Connect components to rate group for periodic execution
rateGroup.set_RateGroupMemberOut_OutputPort(0, compA.get_schedIn_InputPort());
rateGroup.set_RateGroupMemberOut_OutputPort(1, compB.get_schedIn_InputPort());

// Drive rate group from rate group driver
rgDriver.set_CycleOut_OutputPort(0, rateGroup.get_CycleIn_InputPort());
```

### Command/Event/Telemetry Infrastructure
Standard pattern: Connect all commanding components to dispatcher in parallel arrays, all eventing components to event logger, all telemetry to TlmChan.

### Hub Pattern for Cross-Boundary Communication
Connect typed ports through hub's serialization ports to communicate across processes, cores, or devices.

## How to apply

1. **Follow exact order:** Instantiate → Init → Interconnect → Register → Load Params → Start threads
2. **Init before connect:** Components must be initialized before ports connected
3. **Queue depth sizing:** Consider message rate and processing time. Too small = overflow. Too large = wasted memory.
4. **Priority assignment:** Higher priority for time-critical components (rate groups usually highest)
5. **Start order:** Start higher priority active components first
6. **Port connection validation:** Use FPP topology validation to catch wiring errors at compile time
7. **Graceful shutdown:** Call exit() on active components before destroying them
