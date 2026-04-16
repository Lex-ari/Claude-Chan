---
name: F' Command Sequencer Architecture
description: CmdSequencer component for executing timed command sequences from files
type: reference
---

# F' Command Sequencer Architecture

The F' command sequencer executes sequences of commands from binary files stored in the file system. Sequences can contain immediate, relative-time, or absolute-time commands.

## Svc::CmdSequencer Component (Svc/CmdSequencer/docs/sdd.md)

**Purpose:** Execute command sequences from binary files with timing control

**Requirements:**
- ISF-CMDS-001: Read sequence files
- ISF-CMDS-002: Validate sequence files with CRC
- ISF-CMDS-003: Provide command to validate sequence files without running
- ISF-CMDS-004: Cancel sequence upon receiving failed command status
- ISF-CMDS-005: Provide command to cancel existing sequence
- ISF-CMDS-006: Provide overall sequence timeout

**Ports:**
- `cmdIn` (input, async): Framework command input
- `cmdResponseOut` (output): Framework command response
- `comCmdOut` (output): Sends command buffers (Fw::Com) for each command in sequence
- `cmdResponseIn` (input, async): Receives status of last dispatched command
- `seqRunIn` (input, async): Receives requests for running sequences from other components
- `seqDone` (output): Outputs status of sequence run (Fw::CmdResponse)
- `schedIn` (input, async): Scheduler input - checks timed commands
- `pingIn`/`pingOut`: Health check ports

**Commands:**
- **CS_Validate:** Validate sequence file format and checksum without executing
- **CS_Run:** Execute a sequence (cancels any prior sequence)
- **CS_Cancel:** Cancel currently executing sequence
- **CS_Manual:** Enter manual stepping mode
- **CS_Start:** Execute first command in manual mode
- **CS_Step:** Execute next command in manual mode
- **CS_Auto:** Return to automatic mode (can only run when no sequence executing)

**Configuration methods:**
- `setTimeout(seconds)`: Set command timeout (default 0 = no timeout)
- `setSequenceFormat(Sequence&)`: Use custom sequence format (default: FPrimeSequence)
- `allocateBuffer(MemAllocator)`: Provide memory allocator for sequence buffer
- `loadSequence(filename)`: Pre-load sequence into buffer (for later execution via `seqRunIn`)
- `deallocateBuffer()`: Deallocate buffer before destructor

## Sequence Execution Modes

### Automatic Mode (Default)
Sequences execute automatically upon loading:
1. Load sequence file
2. Validate format and CRC
3. Execute commands according to timing
4. Report status when complete/failed

### Manual Mode
Operator controls command-by-command execution:
1. **CS_Manual:** Enter manual mode
2. **CS_Run:** Load and validate sequence (but don't execute)
3. **CS_Start:** Execute first command
4. **CS_Step:** Execute each subsequent command
5. **CS_Auto:** Return to automatic mode (when no sequence running)

**Use case:** Allows careful step-by-step sequence execution during critical operations or testing.

## F Prime Sequence Format

### Header (11 bytes)

| Field | Size | Description |
|-------|------|-------------|
| File Size | 4 | Size of command record buffer following header |
| Number of records | 4 | Number of records in file |
| Time Base | 2 | Time base for sequence (0xFFFF = don't care) |
| Context | 1 | Context for sequence (project-specific, 0xFF = don't care) |

**Note:** All numbers in big-endian format.

### Record Types

#### Descriptor Values
- **0:** Absolute time command
- **1:** Relative time command
- **2:** End of sequence (marker)

#### Record Format (variable length)

| Field | Size | Description |
|-------|------|-------------|
| Descriptor | 1 | Record type (0/1/2) |
| Command Time | 8 | Start time (first 4 bytes = seconds, last 4 bytes = microseconds) |
| Record Size | 4 | Size of command buffer |
| Command Buffer | ≥4 | Command packet descriptor, opcode, serialized arguments |

**Timing interpretation:**
- **Absolute time:** Time is absolute spacecraft time (UTC epoch 1970-01-01)
- **Relative time:** Time is delay from previous command (first command: delay from sequence start)

### CRC (4 bytes)
Last 4 bytes of file is CRC of entire file (computed by `Utils/Hash.hpp`).

## Sequence File Generation

Use `fprime-seqgen` utility to convert text files to binary sequences:

```bash
fprime-seqgen --help
```

### Text Sequence Syntax

**Comment:**
```
; This is a comment
```

**Relative time command:**
```
RHH:MM:SS.FFFF MNEMONIC arg1,arg2,...,argN
```
- R = Relative time descriptor
- HH = hours delay
- MM = minutes delay
- SS = seconds delay
- .FFFF = fractional seconds (optional)

**Immediate command (zero delay):**
```
R00:00:00 MNEMONIC arg1,arg2,...,argN
```

**Absolute time command:**
```
AYYYY-DOYTHH:MM:SS.FFFF MNEMONIC arg1,arg2,...,argN
```
- A = Absolute time descriptor
- YYYY = Year
- DOY = Day of year (001-366)
- Time in UTC with epoch 1/1/1970

## Sequence Execution Flow

```
CS_Run command received
  └─> Load sequence file
      └─> Validate format and CRC
          └─> If valid:
              ├─> Execute commands according to timing
              │   └─> For each command:
              │       ├─> Wait for timing (if relative/absolute)
              │       ├─> Send command via comCmdOut
              │       ├─> Wait for cmdResponseIn
              │       └─> If command fails: ABORT sequence
              └─> Sequence complete (or failed)
                  └─> Send cmdResponseOut with status
```

**schedIn port role:**
- Called periodically (e.g., 10Hz)
- Checks if timed command is ready to execute
- Checks command timeout timer
- Dispatches command when timer expires

## Sequence Abort Conditions

Sequence automatically aborts if:
1. Command returns failed status
2. Command timeout expires (if configured)
3. **CS_Cancel** command received
4. Invalid sequence file format/CRC

**Why auto-abort on command failure?** Subsequent commands may depend on success of previous commands. Continuing could lead to unsafe state.

## seqRunIn Port Behavior

The `seqRunIn` port allows other components to trigger sequence execution.

**Arguments:**
- `filename` (Fw::String): Sequence file to run

**Special behavior:**
- If `filename` is empty AND sequence was pre-loaded via `loadSequence()`:
  - Runs the pre-loaded sequence without re-loading from file
  - Useful for reducing file system access latency
- Otherwise: Loads and runs specified file (same as **CS_Run** command)

## Component Sequence Abstraction

The CmdSequencer uses an abstract `Sequence` class:

**Pure virtual methods:**
- `loadFile(filename)`: Load and validate sequence file
- `hasMoreRecords()`: Check if more records available
- `nextRecord()`: Return next record
- `reset()`: Reset to beginning of sequence
- `clear()`: Clear current sequence

**Default implementation: FPrimeSequence**
Implements F Prime binary format as described above.

**Custom implementations:**
Projects can derive from `Sequence` to support custom formats:
- Different binary encoding
- Different timing models
- Streaming from disk vs. loading into memory
- Runtime sequence generation

Use `setSequenceFormat()` to install custom implementation.

## Sequence Best Practices

**File validation:**
- Always use **CS_Validate** on new sequences before flying
- Verify CRC to detect file corruption
- Test sequences in simulation before flight

**Timeout configuration:**
- Set reasonable command timeout (e.g., 30 seconds)
- Prevents sequence from hanging on unresponsive component
- Zero timeout = no timeout (risky for flight)

**Error handling:**
- Monitor sequence completion events
- Have contingency for sequence abort
- Consider using manual mode for critical sequences

**Timing considerations:**
- Relative timing is resilient to clock changes
- Absolute timing requires accurate spacecraft clock
- Leave margin in timing for command execution
- Consider worst-case command execution time

**How to apply:**
- Use sequencer for planned operations (deployments, mode changes, calibrations)
- Keep individual sequences focused on single operational objective
- Break complex operations into multiple sequences
- Validate sequences extensively before flight
- Monitor sequence progress via events and telemetry
- Have ground procedures for handling sequence failures
