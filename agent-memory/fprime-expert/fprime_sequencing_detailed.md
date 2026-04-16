---
name: F Prime Command Sequencing Detailed
description: Command sequencing architecture, validation, execution modes, timing, and off-nominal behavior
type: reference
---

# F Prime Command Sequencing Detailed

Command sequencing enables ordered, timed execution of multiple commands together.

## Architecture Overview

### Key Components

1. **Svc::SeqDispatcher**: Coordinates execution of multiple sequences
   - Routes sequence files to available sequencer instances
   - Manages pool of sequence "engines"
   - Rejects sequences if no engines available

2. **Svc::CmdSequencer**: Executes individual sequences
   - One sequence at a time per instance
   - Reads sequence file from filesystem
   - Sends commands to CmdDispatcher
   - Waits for command responses
   - Handles timing (relative/absolute)

3. **Svc::CmdDispatcher**: Dispatches commands to handling components
   - Receives commands from ground OR sequencer
   - Routes to appropriate component
   - Returns status to caller (ground or sequencer)

### Sequence Flow

```
Sequence File (filesystem)
    ↓
SeqDispatcher (route to available engine)
    ↓
CmdSequencer (load, validate, execute)
    ↓
CmdDispatcher (dispatch each command)
    ↓
Component (execute command, return status)
    ↓
CmdSequencer (wait for response, proceed or abort)
```

## Sequence Management

### Sequence Storage
- **Location:** Files in filesystem
- **Management:** Via file system functionality
- **Partitioning:** Stored in defined filesystem partitions
- **Size limit:** Configurable at compile time (e.g., in `RefTopology.cpp`)

**Configuration example:**
```cpp
// Maximum sequence buffer size
cmdSeq.allocateBuffer(
    0,
    mallocator,
    MAX_SEQ_BUFFER_SIZE  // Compile-time configuration
);
```

### Sequence File Format

Binary format containing:
- File CRC (for validation)
- Command records with timing information
- Serialized command arguments

**See:** [F Prime Sequence Format documentation] for detailed binary layout

## Validation

Sequences validated before execution. All checks must pass or sequence rejected.

### Validation Checks

1. **CRC Check**
   - File data CRC must match CRC in sequence file
   - Detects corruption during upload/storage
   - Failure: Sequence not loaded

2. **Opcode Validation**
   - All opcodes must be valid in current FSW build
   - Checks against command dispatcher registry
   - Failure: Sequence not loaded (prevents attempting invalid commands)

3. **Argument Deserialization**
   - Arguments must be correct size for command
   - Verifies data integrity
   - Failure: Sequence not loaded

**Result:** If ANY validation check fails, sequence does not load and error reported.

## Execution Modes

### Auto Mode (Default)
Sequencer executes entire sequence without waiting for ground input.

**Behavior:**
- Automatically proceeds to next command after previous completes
- Respects timing directives (relative/absolute)
- Blocks on command until complete (if blocking enabled)
- Terminates on any command failure

**Use case:** Standard sequence execution

### Manual Mode
Sequencer executes one command at a time, waiting for ground command to proceed.

**Behavior:**
- Execute command when ground sends "step" command
- Wait for command completion
- Require ground "step" command for next command
- Allows ground operator to control pace

**Use case:** Testing, cautious execution, step-by-step verification

### Mode Switching

**How:** Via command to sequencer component before sequence start

**Restriction:** Cannot change mode while sequence in progress (rejected)

**Typical commands:**
- `CS_AUTO`: Set to auto mode
- `CS_MANUAL`: Set to manual mode

## Sequence Timing

F Prime sequences support two timing modes: relative and absolute.

### Absolute Time
**Definition:** UTC time when command should execute

**Behavior:**
- Command executes at specified absolute time
- Converted to spacecraft time via spacecraft clock
- If time in past: Execute immediately

**Use case:** 
- Commands at specific time points
- Coordinated activities across spacecraft
- Time-critical operations

**Example:** "Take image at 2024-03-15 14:30:00 UTC"

### Relative Time
**Definition:** Seconds delay before executing command

**Behavior depends on mode and configuration:**

#### Manual Mode - Relative Time
- Execute X seconds after receiving "step" command from ground
- Timer starts when step command received

#### Auto Mode - Blocking Enabled - Relative Time
- Execute X seconds after PREVIOUS COMMAND COMPLETES
- Timer starts when command completion response received
- Sequencer waits for each command before proceeding

#### Auto Mode - Blocking Disabled - Relative Time
- Execute X seconds after COMMAND DISPATCH
- Timer starts when command sent to dispatcher
- Does not wait for command completion
- Allows concurrent command execution

**Why relative time useful:**
- Commands relative to sequence start or previous command
- Flexible timing without knowing absolute time
- Easier sequence authoring for relative operations

**Example:** "Wait 5 seconds after heater on, then check temperature"

### Blocking Configuration

**Blocking enabled (default):**
- Sequencer waits for command response before proceeding
- Ensures command complete before next command
- Relative time based on completion

**Blocking disabled:**
- Sequencer does not wait for command response
- Sends next command immediately (after relative delay)
- Relative time based on dispatch
- Allows command overlap

**Configured:** Via command or configuration before sequence runs

## Off-Nominal Behavior

### Command Failure in Sequence

**Behavior:** If any command in sequence fails, sequence IMMEDIATELY ABORTS.

**Why:** Safety - don't continue if precondition failed.

**Example:**
- Command 1: Enable heater → SUCCESS
- Command 2: Check heater status → FAILURE
- Command 3: Start experiment → NOT EXECUTED (sequence aborted)

**Event emitted:** Sequence failure event with command that failed

### Sequence Abortion

Can be commanded to abort sequence manually:
- Via ground command
- Sequence aborts immediately
- No further commands executed

### Rate Group Overrun / Timeout

If sequencer component doesn't get CPU time:
- Commands may miss timing windows
- Timeout can occur waiting for response
- Depends on threading/priority configuration

## Component Configuration

### Multiple Sequencers

Typical configuration:
- One `SeqDispatcher`
- Multiple `CmdSequencer` instances (e.g., 2-4)
- Each sequencer assigned to dispatcher

**Why multiple:** Execute multiple sequences concurrently (each sequencer handles one sequence)

**Dispatcher routing:** 
- Receives sequence run command
- Finds available sequencer
- Routes sequence to that sequencer
- If all busy: Reject sequence run request

### Sequencer Instance Setup

Each `CmdSequencer`:
1. Connected to SeqDispatcher
2. Connected to CmdDispatcher (for sending commands)
3. Connected to FileManager (for reading sequence files)
4. Configured with buffer size for sequences

## Sequencer Lifecycle

1. **Load:** Ground commands sequence load (or via command)
2. **Validate:** Sequencer performs CRC, opcode, argument checks
3. **Armed:** Sequence ready to run
4. **Run:** Ground commands sequence run (or auto-run)
5. **Execute:** Sequencer sends commands one by one
6. **Complete:** All commands executed successfully, OR
7. **Abort:** Command failed or abort commanded

## Integration with Command System

Sequencer is parallel path to ground commanding:

```
Ground → CmdDispatcher → Component (direct commanding)

Sequence File → SeqDispatcher → CmdSequencer → CmdDispatcher → Component (sequenced commanding)
```

**From CmdDispatcher perspective:** No difference between ground command and sequenced command.

**Command response:** Returns to original caller (ground interface OR sequencer)

## Common Sequence Patterns

### Time-Based Activities
Commands at specific times of day using absolute time.

### Conditional Sequences
Sequence A executes, based on result ground sends Sequence B or C.

### Background Activities
Blocking disabled, commands overlapped for efficiency.

### Critical Sequences
Manual mode, operator verifies each step.

### Repeated Activities
Loop via commanding new sequence at end of previous.

## How to apply

1. **Validate before flight:** All validation checks done at load time, not execute time
2. **Design for failure:** Any command failure aborts sequence - design accordingly
3. **Choose timing wisely:** Absolute for time-critical, relative for sequenced operations
4. **Manual for testing:** Use manual mode during testing/verification
5. **Auto for operations:** Use auto mode for routine operations
6. **Multiple sequencers:** Configure enough sequencer instances for concurrent needs
7. **Monitor events:** Sequencer emits events for load, start, complete, abort
8. **File management:** Use FileUplink to upload sequence files to spacecraft
9. **Sequence generation:** Use ground tools (seqgen) to create valid sequence files
10. **Blocking mode:** Enable blocking (default) unless need concurrent command execution
