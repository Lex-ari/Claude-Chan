---
name: F Prime CmdSequencer Command Sequence Execution
description: CmdSequencer file format, timing modes, sequence execution state machine, and manual stepping
type: reference
---

# Svc::CmdSequencer Command Sequence Execution

## Location
- SDD: `fprime/Svc/CmdSequencer/docs/sdd.md`
- FPP: `fprime/Svc/CmdSequencer/CmdSequencer.fpp`

## Purpose
Executes command sequences from binary files containing timed commands. Supports immediate, relative-timed, and absolute-timed commands.

## Component Type
**Active component** - Has own thread and message queue

## Key Ports

### Input Ports
- `cmdResponseIn: Fw.CmdResponse (async)` - Receives command completion status
- `schedIn: Svc.Sched (async)` - Periodic call to check timers
- `seqRunIn: Svc.CmdSeqIn (async)` - Port-based sequence execution request
- `seqDispatchIn: Svc.FileDispatch (async)` - File-based sequence execution request
- `seqCancelIn: Svc.CmdSeqCancel (async)` - Cancel current sequence

### Output Ports
- `comCmdOut: Fw.Com` - Sends command buffers to CommandDispatcher
- `seqDone: Fw.CmdResponse` - Notifies when sequence completes (for seqRunIn)
- `seqStartOut: Svc.CmdSeqIn` - Notifies when sequence starts

## Sequence File Format (F Prime Binary Format)

### Header (11 bytes)

| Field | Size | Description |
|-------|------|-------------|
| File Size | 4 | Size of command record buffer |
| Number of Records | 4 | Number of records in file |
| Time Base | 2 | Time base for sequence (0xFFFF = don't care) |
| Context | 1 | Context for sequence (0xFF = don't care) |

### Record Format

| Field | Size | Description |
|-------|------|-------------|
| Descriptor | 1 | 0=absolute time, 1=relative time, 2=end of sequence |
| Command Time | 8 | Absolute or relative time (4 bytes seconds + 4 bytes microseconds) |
| Record Size | 4 | Size of command buffer |
| Command Buffer | Variable | Serialized command packet (opcode + arguments) |

**End of File:** 4-byte CRC of entire file

## Sequence Execution Modes

### Auto Mode (Default)
- Commands execute automatically according to timing
- Immediate commands execute as soon as previous completes
- Relative commands wait for delay
- Absolute commands wait for specific time

### Manual Mode (Step Mode)
- Activated by `CS_Manual` command
- Sequence loads but doesn't execute
- `CS_Start` executes first command
- `CS_Step` executes each subsequent command
- `CS_Auto` returns to auto mode

**Mode Enum:**
```fpp
enum SeqMode {
    STEP = 0
    AUTO = 1
}
```

## Sequence Execution State Machine

### States
1. **IDLE** - No sequence loaded
2. **LOADED** - Sequence file loaded and validated
3. **WAITING** - Waiting for command timer to expire
4. **COMMAND_DISPATCHED** - Command sent, waiting for status
5. **ERROR** - Sequence aborted due to error

### Transitions

**IDLE → LOADED:**
- Trigger: `CS_Run` command or `seqRunIn` port call
- Action: Load and validate sequence file

**LOADED → WAITING (Auto mode):**
- Trigger: Automatic
- Action: Start timer for first command

**LOADED → WAITING (Manual mode):**
- Trigger: `CS_Start` command
- Action: Start timer for first command

**WAITING → COMMAND_DISPATCHED:**
- Trigger: `schedIn` detects timer expired
- Action: Send command via `comCmdOut`

**COMMAND_DISPATCHED → WAITING:**
- Trigger: `cmdResponseIn` receives OK status
- Action: Advance to next command, start timer

**COMMAND_DISPATCHED → ERROR:**
- Trigger: `cmdResponseIn` receives error status
- Action: Abort sequence, emit error event

**WAITING → WAITING (Step mode):**
- Trigger: `CS_Step` command
- Action: Immediately expire timer, dispatch command

**Any State → IDLE:**
- Trigger: `CS_Cancel` command
- Action: Cancel sequence, reset state

## Command Timing

### Immediate Commands
- Descriptor: 1 (relative)
- Time: 0:00:00.0000
- Execution: Dispatch immediately after previous command completes

### Relative Time Commands
- Descriptor: 1 (relative)
- Time: HH:MM:SS.FFFF (delay)
- Execution: Wait specified delay after previous command completes

### Absolute Time Commands
- Descriptor: 0 (absolute)
- Time: YYYY-DOY-HH:MM:SS.FFFF (UTC, epoch 1970-01-01)
- Execution: Wait until specific time reached

### Timer Checking
- `schedIn` handler called periodically (typically 1 Hz or faster)
- Compares current time to command time
- Dispatches command when time reached or exceeded

## Command Timeout

**Configuration:** `setTimeout(seconds)`

**Purpose:** Abort sequence if command doesn't complete within timeout

**Mechanism:**
1. When command dispatched, start timeout timer
2. `schedIn` handler checks timeout timer
3. If expired before status received:
   - Emit warning event
   - Abort sequence

**Default:** 0 (no timeout)

## Sequence Validation

**Command:** `CS_Validate(fileName)`

**Purpose:** Validate sequence file without executing

**Algorithm:**
1. Load sequence file
2. Verify file format (header, records, CRC)
3. Check CRC matches
4. Report validation result
5. Do NOT execute commands

**Use Case:** Pre-validate sequences before critical operations

## Sequence Cancellation

**Command:** `CS_Cancel`

**Behavior:**
- Stops current sequence execution
- If no sequence running, emits warning (does not fail)
- Resets state to IDLE

**Note:** Cannot cancel commands already dispatched and awaiting response

## Port-Based Sequence Execution

**Port:** `seqRunIn: Svc.CmdSeqIn`

**Signature:** `seqRunIn(fileName: string)`

**Behavior:**
- Same as `CS_Run` command
- Returns status via `seqDone` port
- Allows component-to-component sequence triggering

**Special Case: Empty fileName:**
- Runs sequence already loaded via `loadSequence()`
- Allows pre-loading sequence for quick execution

## Sequence Format Configuration

**Method:** `setSequenceFormat(Sequence& format)`

**Purpose:** Allows custom sequence format implementation

**Default:** `FPrimeSequence` (F Prime binary format)

**Customization:**
1. Implement `CmdSequencer::Sequence` abstract class
2. Override: `loadFile()`, `hasMoreRecords()`, `nextRecord()`, `reset()`, `clear()`
3. Pass instance to `setSequenceFormat()`
4. Enables project-specific formats or on-demand loading from disk

## Buffer Management

**Method:** `allocateBuffer(Fw::MemAllocator&)`

**Purpose:** Provide memory allocator for sequence buffer

**Required:** Must be called before loading sequences

**Example:**
```cpp
Fw::MallocAllocator allocator;
cmdSequencer.allocateBuffer(allocator);
```

**Deallocation:** `deallocateBuffer()` before destructor

## Blocking State

**Enum:** `BlockState`
- `BLOCK` - Sequence blocks until complete
- `NO_BLOCK` - Sequence runs in background

**Purpose:** Allows sequences to block or run asynchronously

## File Read Stage (for diagnostics)

**Enum:** `FileReadStage`

Tracks which part of file read is in progress:
- `READ_HEADER`
- `READ_HEADER_SIZE`
- `DESER_SIZE`
- `DESER_NUM_RECORDS`
- `DESER_TIME_BASE`
- `DESER_TIME_CONTEXT`
- `READ_SEQ_CRC`
- `READ_SEQ_DATA`
- `READ_SEQ_DATA_SIZE`

**Purpose:** Detailed error reporting for file load failures

## Events

### Sequence Lifecycle
- `CS_SequenceLoaded` - Sequence file loaded successfully
- `CS_SequenceComplete` - Sequence completed successfully
- `CS_SequenceCanceled` - Sequence canceled by command

### Errors
- `CS_FileReadError` - Error reading sequence file
- `CS_FileInvalid` - File format or CRC invalid
- `CS_RecordInvalid` - Invalid record in sequence
- `CS_TimeBaseMismatch` - Time base doesn't match system
- `CS_TimeContextMismatch` - Time context mismatch
- `CS_CommandError` - Command returned error status
- `CS_CommandTimeout` - Command timeout expired

## Sequence Generation Tool

**Tool:** `fprime-seqgen`

**Input:** Text file with command mnemonics and timing

**Output:** Binary sequence file

**Syntax:**
```
; Comment
R00:00:05 CMD_NO_OP
R00:00:00 CMD_TEST 10, 3.14, 255
A2026-100-12:30:00 CMD_TIMED_TEST
```

**Format:**
- `;` - Comment
- `R` - Relative time
- `A` - Absolute time
- `HH:MM:SS.FFFF` - Time specification
- `MNEMONIC` - Command name from dictionary
- `ARG1, ARG2, ...` - Command arguments

## Critical Design Patterns

### 1. Command Status Tracking
- Sequence waits for each command to complete
- Abort on any command failure
- Prevents cascading failures

### 2. Multiple Timing Modes
- Immediate: No delay
- Relative: Delay from previous
- Absolute: Wait for specific time
- Covers all operational scenarios

### 3. Manual Stepping for Debug
- Load sequence without execution
- Step through commands one at a time
- Critical for testing and debugging

### 4. Validation Before Execution
- Pre-validate sequences
- Catch errors before critical operations
- Separate validation from execution

### 5. Timeout Protection
- Prevents hanging on unresponsive commands
- Configurable per deployment
- Graceful abort on timeout

### 6. CRC File Protection
- Detects corrupted sequence files
- Prevents executing invalid commands
- Computed over entire file

### 7. Pluggable Sequence Format
- Abstract `Sequence` class
- Allows custom formats
- Enables on-demand loading strategies

## Common Usage Patterns

### Ground Operations:
1. Upload sequence file to spacecraft
2. Ground → `CmdSequencer.CS_Validate` (verify file)
3. Ground → `CmdSequencer.CS_Run` (execute sequence)
4. Monitor events for progress
5. `CmdSequencer.CS_Cancel` if needed

### Component-Triggered Sequences:
1. Component → `seqRunIn` port
2. CmdSequencer loads and executes
3. CmdSequencer → `seqDone` port (status)
4. Component receives completion status

### Manual Stepping (Debug):
1. Ground → `CmdSequencer.CS_Manual`
2. Ground → `CmdSequencer.CS_Run` (load only)
3. Ground → `CmdSequencer.CS_Start` (first command)
4. Ground → `CmdSequencer.CS_Step` (each subsequent)
5. Ground → `CmdSequencer.CS_Auto` (resume auto)

**How to apply:** When creating sequences:
1. Use `fprime-seqgen` to generate binary from text
2. Always validate before critical execution
3. Set appropriate timeout based on expected command duration
4. Consider manual mode for first execution of new sequences
5. Handle command failures in sequence design (avoid dependencies)
