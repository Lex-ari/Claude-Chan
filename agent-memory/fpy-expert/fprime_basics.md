---
name: FPrime Basics
description: What F Prime is and how Fpy integrates with it
type: reference
---

# F Prime (FPrime) Overview

## What is F Prime?

F Prime is a **component-driven framework** developed at JPL (Jet Propulsion Laboratory) that enables rapid development and deployment of spaceflight and embedded software applications. It has been successfully deployed on several space missions, particularly CubeSats, SmallSats, and instruments.

**Key Characteristics:**
- Component-based architecture with well-defined interfaces
- C++ framework providing core capabilities (message queues, threads, etc.)
- Modeling tools for specifying components and auto-generating code
- Collection of ready-to-use components
- Testing tools for unit and integration testing

## Core F Prime Concepts

### Components
F Prime applications are built from **components** - modular units that:
- Communicate through typed **ports**
- Can be **active** (have their own thread) or **passive**
- Are defined using **FPP** (F Prime Prime) modeling language
- Have commands, events, telemetry, and parameters

### Commands
Commands are instructions sent to components to perform actions. They:
- Have opcodes (operation codes) that identify them
- Can have typed arguments
- Return command responses (OK, EXECUTION_ERROR, etc.)
- Are dispatched through the command dispatcher

### Telemetry
Telemetry channels are named values that components publish to monitor system state.

### Parameters
Parameters are configuration values that can be saved to persistent storage and loaded at runtime.

### Sequencing
F Prime provides command sequencing capability through **sequencer components** that execute ordered lists of commands with specific timing.

## Fpy's Role in F Prime

Fpy is a **high-level scripting language** that compiles to bytecode for execution by the `FpySequencer` component in F Prime. It provides:

1. **Expressive syntax** - Python-like language vs. simple command lists
2. **Control flow** - If/else, loops, functions, etc.
3. **Type safety** - Static typing with compile-time checks
4. **Telemetry/parameter access** - Read spacecraft state within sequences
5. **Math and logic** - Perform calculations and conditionals
6. **Complex data structures** - Work with structs, arrays, enums from the F Prime dictionary

## Traditional F Prime Sequencing vs Fpy

### Traditional CmdSequencer
- Located in: `/lib/fprime/Svc/CmdSequencer/`
- Executes simple sequence files (`.seq` format)
- Commands with relative/absolute timing
- Limited control flow
- Validation based on opcode checking and CRC

### Fpy + FpySequencer
- Located in: `/lib/fprime/Svc/FpySequencer/`
- Executes compiled Fpy bytecode (`.bin` files)
- Full programming language features (variables, functions, conditionals, loops)
- Stack-based virtual machine
- Access to telemetry and parameters within sequences
- Bytecode validation with schema versioning

## Architecture Layers

```
.fpy source files (user writes)
        ↓
fprime-fpyc compiler (Python)
        ↓
.bin bytecode files
        ↓
FpySequencer component (C++)
        ↓
F Prime command dispatcher
        ↓
Target components
```

## Key F Prime Directories

- `/lib/fprime/Svc/` - Service components (including FpySequencer)
- `/lib/fprime/Fw/` - Framework core types and utilities
- `/lib/fprime/Drv/` - Driver components
- `/lib/fprime/Ref/` - Reference deployment example
- `/lib/fprime/docs/` - Documentation

## Integration Points

The FpySequencer integrates with F Prime through:
1. **Command output port** (`cmdOut: Fw.Com`) - sends commands for dispatch
2. **Command response port** (`cmdResponseIn: Fw.CmdResponse`) - receives command completion status
3. **Telemetry get port** (`getTlmChan: Fw.TlmGet`) - reads telemetry values
4. **Parameter get port** (`getParam: Fw.PrmGet`) - reads parameter values
5. **Timer port** (`checkTimers: Svc.Sched`) - triggered by rate group for timing
6. **Standard ports** - time, events, telemetry, parameters
