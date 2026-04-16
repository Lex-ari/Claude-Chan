---
name: F' Framework Comprehensive Overview
description: High-level summary of F' framework architecture, philosophy, and key components
type: reference
---

# F' Framework Comprehensive Overview

NASA JPL's F Prime (F') is a component-based flight software framework used for spacecraft and embedded systems.

## Framework Philosophy

**Core Principles:**
1. **Component-based architecture** - Self-contained modules with defined interfaces
2. **Port-based communication** - Typed interfaces prevent mismatches
3. **Separation of concerns** - Interface (FPP) vs implementation (C++) vs wiring (topology)
4. **Reusability** - Framework components work across missions
5. **Testability** - Components testable in isolation via port mocks

## Key Framework Subsystems

### 1. Commanding (Fw/Cmd, Svc/CmdDispatcher, Svc/CmdSequencer)
- **CmdDispatcher**: Routes commands from ground/sequencer to components
- **CmdSequencer**: Executes timed command sequences from files
- Components register opcodes, receive commands, report status
- Two-phase flow: registration → dispatch/response

### 2. Event Reporting (Fw/Log, Svc/ActiveTextLogger)
- Seven severity levels (FATAL → DIAGNOSTIC)
- Binary (Fw::Log) and text (Fw::LogText) paths
- ActiveTextLogger writes to console/file with rotation
- Events are non-blocking (async ports)

### 3. Telemetry (Fw/Tlm, Svc/TlmChan)
- TlmChan stores all channel values in double-buffered hash table
- Components write channels individually when values change
- TlmChan periodically packages changed channels for downlink
- Efficient: O(1) lookup, minimal bandwidth

### 4. Parameters (Fw/Prm, Svc/PrmDb)
- PrmDb stores parameters in file and memory
- Components load parameters during initialization
- Updates in memory; explicit save command to persist
- Two-phase: load from file → runtime updates → save to file

### 5. Rate Groups (Svc/RateGroupDriver, Svc/ActiveRateGroup)
- RateGroupDriver divides system tick into multiple rates
- ActiveRateGroup drives periodic component execution
- Each rate group has dedicated thread (async decoupling)
- Cycle slip detection for overruns

### 6. Health Monitoring (Svc/Health)
- Pings active components periodically
- Timeout indicates hung thread or full queue
- FATAL event on timeout
- Strokes watchdog when all components healthy

### 7. File Management (Svc/FileUplink, Svc/FileDownlink)
- Packet-based file transfer (START/DATA/END/CANCEL)
- Checksum validation (CCSDS CFDP method)
- Queue management with cooldown
- FileManager for on-board file operations

## Component Types

| Type | Thread | Queue | Use Case |
|------|--------|-------|----------|
| **Passive** | None | None | Simple utilities, stateless functions |
| **Queued** | None | Yes | Rare - queue without thread |
| **Active** | Yes | Yes | Most flight software (async behavior) |

**Threading model:**
- Async ports enqueue messages → component thread dispatches
- Sync ports execute on caller's thread
- Guarded ports add mutex protection to sync ports

## Port Patterns

**Port kinds:**
- **Synchronous**: Fast, blocking, can return values
- **Asynchronous**: Non-blocking, queued, no return values
- **Guarded**: Synchronous with mutex protection

**Threading implications:**
- Sync on passive: Executes on caller's thread
- Async on active: Enqueues message, dispatches on component's thread
- Critical for understanding component behavior and thread safety

## Data Flow Patterns

### Command Flow
```
Ground → Deframer → CmdDispatcher → Component → CmdDispatcher → Ground
                         ↓                 ↓
                    Registration      Command Handler
                                          ↓
                                    cmdResponse_out
```

### Event Flow
```
Component → log_out → EventLogger → Downlink (binary)
          → logText_out → ActiveTextLogger → Console/File (text)
```

### Telemetry Flow
```
Component → tlm_out → TlmChan (stores all channels)
                          ↓
                    Run port (periodic)
                          ↓
                    Package changed channels
                          ↓
                    TlmPacketizer → Downlink
```

### Parameter Flow
```
Initialization:
    PrmDb loads file → Component loadParameters() → getPrm → Component stores values

Runtime:
    Component command → Component updates param → setPrm → PrmDb updates memory
    Ground command → PRM_SAVE_FILE → PrmDb writes file
```

## Critical Framework Patterns

### 1. Serialization
- All data crossing network/file boundaries is serialized
- Big-endian (network byte order)
- Fw::Serializable base class for custom types
- Auto-generated for commands/events/telemetry

### 2. Active Component Lifecycle
```
Construction → init() → preamble() → Message Loop → finalizer() → Destruction
                            ↑                              ↑
                      Before messages              After exit()
```

### 3. Thread Safety
- **Async handlers**: Thread-safe automatically (serialized via queue)
- **Sync handlers**: NOT thread-safe, need guarded ports or mutexes
- **Passive components**: Always need mutexes if multi-threaded

### 4. Component Base IDs
Each component instance gets a base ID for opcodes/channels/events/params.
Framework adds offsets to base ID for unique system-wide identifiers.

### 5. Port Numbering
Components with multiple ports of same type use `portNum` to distinguish:
```cpp
void handler(NATIVE_INT_TYPE portNum, Args...) {
    if (portNum == 0) { /* first port */ }
    else if (portNum == 1) { /* second port */ }
}
```

## Auto-Generated Code

F' autocoder generates from FPP definitions:

**Component base class:**
- Port registration
- Command registration and dispatch
- Event/telemetry/parameter helpers
- Serialization/deserialization

**Topology code:**
- Component instantiation
- Port wiring
- Base ID assignment

**User implements:**
- Component logic in handler methods
- State management
- Algorithms

**Why separation?** User code isolated from framework boilerplate. Regenerating from FPP updates framework integration without touching user logic.

## Framework File Locations

Critical framework files:

```
example-project/fprime/
├── Fw/               # Base types (Cmd, Log, Tlm, Prm, Port, Comp, Time, etc.)
├── Svc/              # Service components (60+ components)
│   ├── CmdDispatcher/
│   ├── CmdSequencer/
│   ├── TlmChan/
│   ├── ActiveRateGroup/
│   ├── RateGroupDriver/
│   ├── Health/
│   ├── FileUplink/
│   ├── FileDownlink/
│   └── ActiveTextLogger/
├── Drv/              # Drivers (GPIO, I2C, SPI, UART, TCP, UDP)
├── Os/               # OS abstraction (Task, Queue, Mutex, File)
└── docs/             # Framework documentation
```

## Common F' Deployments

Every F' deployment includes:

**Minimum set:**
- CmdDispatcher (command routing)
- ActiveLogger or ActiveTextLogger (event logging)
- TlmChan (telemetry storage)
- RateGroupDriver + ActiveRateGroup (periodic scheduling)
- Framer/Deframer (packet framing)
- FileUplink/FileDownlink (file transfer)

**Optional but common:**
- CmdSequencer (sequence execution)
- PrmDb (parameter storage)
- Health (health monitoring)
- FileManager (file operations)
- SystemResources (CPU/memory telemetry)
- Version (version reporting)

## Design Patterns in F'

1. **Hub pattern**: CmdDispatcher, TlmChan centralize routing
2. **Active-passive split**: Active components for async, passive for utilities
3. **Double buffering**: TlmChan uses double buffer for concurrent read/write
4. **Hash tables**: TlmChan, PrmDb use hash tables for O(1) lookup
5. **State machines**: CmdSequencer, FileUplink/Downlink use explicit state machines
6. **Timeout patterns**: CmdSequencer, Health use timeouts for error detection
7. **Cooldown patterns**: FileDownlink uses cooldown to prevent saturation
8. **Queue overflow protection**: CmdDispatcher drops commands when full (DOS protection)

## Testing in F'

**Unit testing:**
- GTest framework
- Mock ports for isolation
- Test harness auto-generated from FPP
- History tracking for verifying events/telemetry

**Integration testing:**
- Full topology with real components
- Simulated drivers
- GDS (Ground Data System) for interactive testing

**How to apply F' knowledge:**
- Start with framework components (don't reinvent CmdDispatcher, TlmChan, etc.)
- Follow framework patterns (component types, port kinds, serialization)
- Read component SDDs before using/modifying framework components
- Understand threading model (passive/queued/active, sync/async ports)
- Test components in isolation first, then integrated
- Use GDS for interactive testing and operations
