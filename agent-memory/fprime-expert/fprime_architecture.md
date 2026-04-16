---
name: F' Framework Architecture Overview
description: Core F' framework structure including directory layout and module organization
type: reference
---

# F' Framework Architecture Overview

F' (F Prime) is NASA JPL's component-based flight software framework. The framework is located at `example-project/fprime/` and has the following structure:

## Top-Level Directory Organization

- **Fw/** - Framework base types and classes (foundation layer)
  - Buffer, Cmd, Com, Comp, Log, Port, Prm, Tlm, Time, Types, etc.
  - Base classes for components, ports, serialization
  - Core packet and data structure definitions

- **Svc/** - Service components (application layer)
  - 60+ reusable service components
  - CmdDispatcher, CmdSequencer, TlmChan, ActiveRateGroup, Health, etc.
  - File management (FileUplink, FileDownlink, FileManager)
  - Communication components (Framer, Deframer, Router)

- **Drv/** - Driver components (hardware abstraction)
  - LinuxGpioDriver, LinuxI2cDriver, LinuxSpiDriver, LinuxUartDriver
  - Network drivers (TcpClient, TcpServer, Udp)
  - ByteStream adapters

- **Os/** - Operating system abstraction layer
  - Task, Queue, Mutex, File, Directory abstractions
  - Platform-independent OS interfaces

- **Utils/** - Utility libraries
  - Hash functions, type conversion utilities

- **CFDP/** - CCSDS File Delivery Protocol implementation

## Framework Philosophy

F' follows a **component-port architecture**:

1. **Components** are self-contained modules with defined interfaces
2. **Ports** are typed interfaces for component communication
3. **Topologies** wire components together via port connections
4. **Serialization** provides language-independent data encoding

The framework enforces separation between:
- Interface definition (FPP files)
- Component logic (C++ implementation)
- System wiring (topology files)

**Why:** This separation enables modularity, reusability, testability, and prevents tight coupling between components.

**How to apply:** When working with F' projects, always distinguish between framework-provided components (Fw/, Svc/, Drv/) and project-specific components. Framework components follow well-established patterns that should be emulated in custom components.
