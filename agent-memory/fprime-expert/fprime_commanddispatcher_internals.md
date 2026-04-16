---
name: F Prime CommandDispatcher Component Internals
description: Deep dive into CmdDispatcher architecture, dispatch tables, sequence tracking, and command flow
type: reference
---

# Svc::CmdDispatcher Component Internals

## Location
- SDD: `fprime/Svc/CmdDispatcher/docs/sdd.md`
- FPP: `fprime/Svc/CmdDispatcher/CmdDispatcher.fpp`
- Implementation: `fprime/Svc/CmdDispatcher/CommandDispatcherImpl.hpp/cpp`

## Purpose
Routes incoming command buffers (Fw::Com) to registered components based on opcode, then routes command completion status back to the command source.

## Component Type
**Active component** - Has its own thread and message queue

## Key Ports

### Input Ports
- `seqCmdBuff[N]: Fw.Com (async)` - Receives encoded command buffers from ground, sequencers, etc.
- `compCmdReg[N]: Fw.CmdReg (guarded)` - Components register their opcodes here
- `compCmdStat: Fw.CmdResponse (async)` - Components report command completion status
- `run: Svc.Sched (async)` - Triggers telemetry emission

### Output Ports
- `compCmdSend[N]: Fw.Cmd` - Sends decoded commands to implementing components
- `seqCmdStatus[N]: Fw.CmdResponse` - Returns command status to command source

### Port Matching
- `compCmdSend` matched with `compCmdReg` - Port number used for registration maps to dispatch port
- `seqCmdStatus` matched with `seqCmdBuff` - Status returned to same port that sent command

## Internal Data Structures

### DispatchEntry Table
**Purpose:** Maps opcodes to component dispatch ports

```cpp
struct DispatchEntry {
    bool used;              // Entry is in use
    FwOpcodeType opcode;    // Command opcode
    FwIndexType port;       // Output port to dispatch to
} m_entryTable[CMD_DISPATCHER_DISPATCH_TABLE_SIZE];
```

**Size:** Configurable via `CMD_DISPATCHER_DISPATCH_TABLE_SIZE`

**Populated by:** Command registration during component initialization

### SequenceTracker Table
**Purpose:** Tracks in-flight commands waiting for completion status

```cpp
struct SequenceTracker {
    bool used;              // Slot is in use
    U32 seq;                // Command sequence number assigned by dispatcher
    FwOpcodeType opCode;    // Opcode being tracked
    U32 context;            // User context value (from command source)
    FwIndexType callerPort; // Port number of command source
} m_sequenceTracker[CMD_DISPATCHER_SEQUENCER_TABLE_SIZE];
```

**Size:** Configurable via `CMD_DISPATCHER_SEQUENCER_TABLE_SIZE`

**Purpose:** Allows dispatcher to route status back to correct source when command completes

### Sequence Counter
- `m_seq` - Current command sequence number (incremented for each dispatched command)
- Assigned to command when dispatched, used to match status responses

## Command Registration Flow

**Triggered by:** Component initialization calling `regCommands()`

**Handler:** `compCmdReg_handler(FwIndexType portNum, FwOpcodeType opCode)`

**Algorithm:**
1. Search for empty slot in `m_entryTable`
2. If found:
   - Set `used = true`
   - Store `opcode`
   - Store `port = portNum` (registration port number)
   - Emit `OpCodeRegistered` event
3. If opcode already registered to same port:
   - Emit `OpCodeReregistered` event (allows re-registration)
4. Assert if duplicate opcode registered to different port
5. Assert if no slots available

**Key Insight:** Port number used for registration determines port used for dispatch

## Command Dispatch Flow

**Triggered by:** Command buffer arriving on `seqCmdBuff` port

**Handler:** `seqCmdBuff_handler(FwIndexType portNum, Fw::ComBuffer& data, U32 context)`

**Algorithm:**
1. **Deserialize command packet:**
   - Extract opcode from buffer
   - If deserialization fails → emit `MalformedCommand` event, return `VALIDATION_ERROR`

2. **Look up opcode in dispatch table:**
   - Search `m_entryTable` for matching opcode
   - If not found → emit `InvalidCommand` event, return `INVALID_OPCODE`

3. **Track command if status port connected:**
   - Search for empty slot in `m_sequenceTracker`
   - Store: `seq = m_seq`, `opCode`, `context`, `callerPort = portNum`
   - If no slots → emit `TooManyCommands` event, return `EXECUTION_ERROR`

4. **Dispatch command:**
   - Call `compCmdSend_out(port, opCode, m_seq, argBuffer)`
   - Emit `OpCodeDispatched` event
   - Increment `m_numCmdsDispatched`

5. **Increment sequence number:** `m_seq++`

## Command Completion Flow

**Triggered by:** Component calling `cmdResponse_out()` after executing command

**Handler:** `compCmdStat_handler(portNum, opCode, cmdSeq, response)`

**Algorithm:**
1. **Check response status:**
   - If `OK` → emit `OpCodeCompleted` event
   - If error → increment `m_numCmdErrors`, emit `OpCodeError` event

2. **Find command in sequence tracker:**
   - Search `m_sequenceTracker` for entry with `seq == cmdSeq`
   - Assert if `opCode` doesn't match
   - Extract `callerPort` and `context`
   - Mark entry as `used = false`

3. **Report status to command source:**
   - If `seqCmdStatus` port connected at `callerPort`:
     - Call `seqCmdStatus_out(callerPort, opCode, context, response)`
   - **Important:** `context` (not `cmdSeq`) is passed back to caller

## Queue Overflow Handling

**Hook:** `seqCmdBuff_overflowHook(portNum, data, context)`

**Behavior:**
- Triggered when message queue is full (DOS protection)
- Deserialize opcode from buffer (best effort)
- Increment `m_numCmdsDropped` counter
- Emit `CommandDroppedQueueOverflow` event (throttled to 5)

**Why:** Prevents queue overflow from crashing system

## Telemetry

Updated by `run_handler()`:
- `CommandsDispatched` - Total commands dispatched
- `CommandErrors` - Total command errors
- `CommandsDropped` - Commands dropped due to queue overflow

## Critical Design Patterns

### 1. Opcode-to-Port Mapping
- Registration port number determines dispatch port number
- Allows multiple components to handle different opcodes
- Dispatch table enables O(N) lookup (could be optimized with hash)

### 2. Sequence Number Assignment
- Dispatcher assigns unique sequence numbers
- Allows tracking command completion even if multiple commands to same component are in flight
- Sequence number links dispatch to completion

### 3. Context Pass-Through
- Command source provides `context` value
- Dispatcher stores it in sequence tracker
- Returns it (not `cmdSeq`) in status response
- Allows command source to track its own requests

### 4. Port Number Matching
- Status must return on same port number as command was received
- Enables multiple command sources (ground, sequencers) to operate independently

### 5. Queue Overflow Protection
- Async port has `hook` defined in FPP
- Provides graceful degradation instead of assertion
- Critical for handling DOS scenarios

## Configuration

**Key defines** (in `config/CommandDispatcherImplCfg.hpp`):
- `CMD_DISPATCHER_DISPATCH_TABLE_SIZE` - Max opcodes in system
- `CMD_DISPATCHER_SEQUENCER_TABLE_SIZE` - Max in-flight commands

**How to apply:** When adding commands to system, ensure dispatch table is large enough. When debugging command timeout issues, check if sequence tracker is full (TooManyCommands event).
