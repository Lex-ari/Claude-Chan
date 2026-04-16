---
name: F' Commanding System Architecture
description: Command registration, dispatch, and response flow including CmdDispatcher behavior
type: reference
---

# F' Commanding System Architecture

The F' commanding system enables ground operators and sequencers to control spacecraft behavior through commands sent to components.

## Key Components and Ports

### Fw::Cmd Port (Fw/Cmd/docs/sdd.md)
- **Purpose:** Send commands with encoded arguments to components
- **Arguments:** Opcode, command sequence number, serialized argument buffer
- **Direction:** CmdDispatcher → Component

### Fw::CmdResponse Port (Fw/Cmd/docs/sdd.md)
- **Purpose:** Report command completion status
- **Arguments:** Opcode, command sequence number, response status
- **Direction:** Component → CmdDispatcher
- **Note:** Also used for `seqCmdStatus` output from CmdDispatcher (context value substituted for cmdSeq)

### Fw::CmdReg Port (Fw/Cmd/docs/sdd.md)
- **Purpose:** Components register their command opcodes
- **Direction:** Component → CmdDispatcher
- **When:** During initialization via auto-generated `regCommands()` function

### Fw::Com Port (Fw/Com/docs/sdd.md)
- **Purpose:** Transport serialized command packets (and other data)
- **Contains:** Fw::ComBuffer with packet data, Fw::ComPacket base class

## Command Flow Architecture

### 1. Command Registration (Initialization)

```
Component Initialization
  └── regCommands() [auto-generated]
      └── For each command opcode:
          └── cmdReg port call → CmdDispatcher
              └── CmdDispatcher stores: opcode → output port mapping
```

**Key insight:** The port number used for command dispatch (compCmdSend) must match the port number used for registration (cmdReg). F' topology autocoder handles this wiring.

### 2. Command Dispatch (Runtime)

```
Ground/Sequencer
  └── seqCmdBuff (Fw::Com) → CmdDispatcher
      └── CmdDispatcher:
          1. Decode opcode from buffer
          2. Look up opcode in dispatch table → find output port
          3. Assign sequence number
          4. Store in pending command table: {opcode, seq#, context, source port}
          5. cmdSend (Fw::Cmd) → Component
              └── Component:
                  1. Execute command handler
                  2. compCmdStat (Fw::CmdResponse) → CmdDispatcher
                      └── CmdDispatcher:
                          1. Match seq# to pending command table
                          2. seqCmdStatus → original source (if connected)
```

**Critical details:**
- CmdDispatcher maintains a **dispatch table** (opcode → port mapping)
- CmdDispatcher maintains a **pending command table** (tracking in-flight commands)
- Sequence numbers are assigned by CmdDispatcher, not by command source
- Context values from seqCmdBuff are passed back via seqCmdStatus (not command seq#)

### 3. Command Response Status Values

Commands return one of these statuses:
- **OK** - Command executed successfully
- **ERROR** - Command failed
- **FATAL** - Fatal error during command execution
- **VALIDATION_ERROR** - Command argument validation failed
- **FORMAT_ERROR** - Command format error
- **EXECUTION_ERROR** - Error during command execution

## Svc::CmdDispatcher Component (Svc/CmdDispatcher/docs/sdd.md)

**Requirements:**
- CD-001: Accept command buffers and decode them
- CD-002: Dispatch commands to components
- CD-003: Provide interface to register commands
- CD-004: Process command status and report results
- CD-005: Drop incoming commands to prevent queue overflow (DOS protection)

**Ports:**
- `seqCmdBuff` (input, async): Receive command buffer from ground/sequencer
- `cmdReg` (input, sync): Command registration
- `cmdSend` (output): Send commands to components
- `compCmdStat` (input, async): Receive command status from components
- `seqCmdStatus` (output): Send status back to command source
- `run` (input, async): Report telemetry

**Key behaviors:**
- Thread-safe command dispatch via message queue
- Supports multiple command sources (multiple seqCmdBuff ports)
- Tracks command timeout and sequence numbers
- Prevents queue overflow by dropping commands when full

**Why:** CmdDispatcher centralizes command routing, enabling one-to-many command distribution, command tracking, and protection against malformed commands.

**How to apply:**
- Every F' deployment includes one CmdDispatcher instance
- Components register commands during init phase before accepting commands
- Command handlers should execute quickly or use async patterns for long operations
- Always report command status (OK/ERROR) from command handlers
- Connection requirement: seqCmdBuff port N must connect to same source as seqCmdStatus port N

## Command Implementation Pattern

In component FPP:
```
async command MY_CMD(arg1: U32, arg2: string)
```

In component C++:
```cpp
void MyComponent::MY_CMD_cmdHandler(
    FwOpcodeType opCode,
    U32 cmdSeq,
    U32 arg1,
    const Fw::CmdStringArg& arg2
) {
    // Execute command logic

    // Report status
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}
```

**Critical:** Always call `cmdResponse_out()` to report command status. Failure to do so will cause CmdDispatcher to wait indefinitely and potentially trigger timeouts.
