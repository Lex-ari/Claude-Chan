---
name: F Prime Framework Architecture Overview
description: Core architecture and directory structure of the NASA JPL F Prime framework
type: reference
---

# F Prime Framework Architecture Overview

## Framework Location
- Framework root: `example-project/fprime/` (or `lib/fprime/` in some projects)
- This is the generic, reusable F Prime framework from NASA JPL

## Key Directories

### Svc/ - Framework Service Components
Contains all standard framework service components:
- **CmdDispatcher** - Command routing and dispatch
- **ActiveRateGroup / PassiveRateGroup** - Periodic execution scheduling
- **TlmChan** - Telemetry channel storage and management
- **PrmDb** - Parameter database
- **Health** - Component health monitoring via ping mechanism
- **CmdSequencer** - Command sequence execution
- **FileManager / FileUplink / FileDownlink** - File transfer system
- **BufferManager** - Buffer pool management
- **EventManager** - Event logging (ActiveLogger is older name)
- **SystemResources** - System resource monitoring
- **FprimeFramer / FprimeDeframer** - Frame encoding/decoding
- **ComQueue / ComStub** - Communication buffering
- And 40+ more specialized components

### Fw/ - Framework Base Classes and Types
Core framework infrastructure:
- **Comp/** - Component base classes (PassiveComponentBase, QueuedComponentBase, ActiveComponentBase)
- **Port/** - Port base class implementation
- **Cmd/** - Command types and packets
- **Tlm/** - Telemetry types
- **Log/** - Event/log types
- **Prm/** - Parameter types
- **Time/** - Time types
- **Buffer/** - Buffer types
- **Types/** - Basic serializable types

### Drv/ - Device Driver Framework
Framework for hardware interface components

### Os/ - Operating System Abstraction Layer
Abstracts OS primitives: Task, Queue, Mutex, File, etc.

### Utils/ - Utility Components
Hash functions, rate limiters, etc.

## Why This Matters
Understanding the framework structure helps distinguish between:
1. **Framework patterns** (apply to ANY F Prime project)
2. **Project-specific implementations** (specific to your project)

When answering questions, always identify whether behavior comes from the framework itself or project-specific code.

**How to apply:** When studying a component, first check if it's in `fprime/Svc/` (framework) or project directories (project-specific). Framework components define standard patterns that all F Prime projects follow.
