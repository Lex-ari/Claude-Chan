---
name: FpySequencer Runtime
description: State machine, execution model, and runtime behavior
type: reference
---

# FpySequencer Runtime Behavior

## Component Overview

**Location:** `/lib/fprime/Svc/FpySequencer/`

The FpySequencer is an **active component** (has its own thread) that loads, validates, and executes Fpy bytecode sequences. It implements a state machine for sequence lifecycle management and a virtual machine runtime for bytecode execution.

## State Machine

### States

**IDLE**
- Entry: Clear breakpoint and sequence file
- No sequence loaded
- Accepts: `SET_BREAKPOINT`, `CLEAR_BREAKPOINT`

**VALIDATING**
- Entry: Report sequence started, begin validation
- Loading and validating bytecode file
- Accepts: `SET_BREAKPOINT`, `CLEAR_BREAKPOINT`, `CANCEL`

**AWAITING_CMD_RUN_VALIDATED**
- Validation succeeded, waiting for RUN_VALIDATED command
- Accepts: `SET_BREAKPOINT`, `CLEAR_BREAKPOINT`, `CANCEL`, `RUN_VALIDATED`

**RUNNING**
- Actively executing sequence
- Has several substates (see below)

### RUNNING Substates

**BREAK_CHECK**
- Check if breakpoint should trigger
- Transitions to PAUSED if break condition met
- Otherwise transitions to DISPATCH_STATEMENT

**DISPATCH_STATEMENT**
- Fetch, decode, and execute next directive
- On success: transition to AWAITING_STATEMENT_RESPONSE
- On failure: exit to IDLE with error
- On no more statements: exit to IDLE with success

**AWAITING_STATEMENT_RESPONSE**
- Waiting for command response (if directive was a command)
- On success: transition to SLEEPING or back to BREAK_CHECK
- On failure/timeout: exit to IDLE with error

**SLEEPING**
- Waiting for relative or absolute time
- Checked on `checkTimers` port invocations
- On wake: transition to BREAK_CHECK
- On timeout/error: exit to IDLE with error

**PAUSED** (debugging state)
- Execution paused at breakpoint
- Entry: Clear break-before-next-line flag
- Accepts: `CONTINUE`, `STEP`

## Commands

### Execution Commands

**RUN** - Load, validate, and run sequence
- Args: `fileName: string`, `block: BlockState`
- Transitions: IDLE → VALIDATING → RUNNING

**VALIDATE** - Load and validate without running
- Args: `fileName: string`
- Transitions: IDLE → VALIDATING → AWAITING_CMD_RUN_VALIDATED

**RUN_VALIDATED** - Run previously validated sequence
- Args: `block: BlockState`
- Transitions: AWAITING_CMD_RUN_VALIDATED → RUNNING

**CANCEL** - Cancel running or validated sequence
- Transitions: VALIDATING/AWAITING_CMD_RUN_VALIDATED/RUNNING → IDLE

### Debugging Commands

**SET_BREAKPOINT** - Pause at specific statement
- Args: `stmtIdx: U32`, `breakOnce: bool`
- Valid in: All states

**BREAK** - Immediately pause before next statement
- Valid in: RUNNING (not PAUSED)

**CONTINUE** - Resume automatic execution
- Valid in: RUNNING.PAUSED

**CLEAR_BREAKPOINT** - Remove breakpoint
- Valid in: All states

**STEP** - Execute one statement then pause
- Valid in: RUNNING.PAUSED

**DUMP_STACK_TO_FILE** - Debug stack contents
- Valid in: Not during automatic execution

### Flag Commands

**SET_FLAG** - Set runtime flag value
- Args: `flag_id: FlagId`, `value: bool`

## Runtime Flags

Flags control sequencer behavior during execution:

**EXIT_ON_CMD_FAIL**
- Default: Configurable via `FLAG_DEFAULT_EXIT_ON_CMD_FAIL` parameter
- If true: Sequence exits with error if command fails
- If false: Sequence continues after command failure

## Ports

### Input Ports

**cmdIn** - Receive commands (standard)
**cmdResponseIn** - Command completion responses (priority 5)
**pingIn** - Health check (priority 10, highest)
**checkTimers** - Rate group for timing (priority 4)
**tlmWrite** - Rate group for telemetry (priority 1, lowest)
**seqRunIn** - Sequence execution requests (priority 7)

### Output Ports

**cmdOut** - Send commands to dispatcher
**seqStartOut** - Notify sequence started
**seqDoneOut** - Notify sequence completed
**pingOut** - Respond to health check
**getTlmChan** - Get telemetry channel value
**getParam** - Get parameter value

### Standard Ports

**timeCaller** - Get current time
**cmdRegOut** - Register commands
**cmdResponseOut** - Send command responses
**logTextOut** - Text events
**logOut** - Binary events
**tlmOut** - Telemetry channels
**prmGet/prmSet** - Parameter database access

## Execution Model

### Directive Dispatch Cycle

1. **Check breakpoint conditions**
2. **Fetch next statement** from sequence
3. **Deserialize directive** and arguments
4. **Validate directive** arguments and state
5. **Execute directive** operation
6. **Update runtime state** (PC, stack, etc.)
7. **Wait for responses** if needed (commands, timers)
8. **Repeat** until sequence complete or error

### Timing Resolution

The sequencer checks timing events (WAIT_REL, WAIT_ABS) only when:
- The `checkTimers` port is invoked (typically by a rate group)

**Temporal Resolution:** Determined by `checkTimers` rate
- Higher rate = more accurate timing
- Lower rate = less CPU overhead

### Command Execution Flow

For command directives (CONST_CMD, STACK_CMD):
1. Serialize command arguments
2. Send command via `cmdOut` port
3. Transition to AWAITING_STATEMENT_RESPONSE
4. Wait for response on `cmdResponseIn` port
5. Check `EXIT_ON_CMD_FAIL` flag if command failed
6. Continue or exit based on flag

### Stack Frame Management

**Function Call:**
1. Execute CALL directive with `func_id`
2. Push return address to stack
3. Set `currentFrameStart` to top of stack
4. Allocate space for function locals
5. Jump to function entry point

**Function Return:**
1. Execute RETURN directive
2. Pop return value (if any) to temp location
3. Restore `currentFrameStart` to caller's frame
4. Restore PC to return address
5. Push return value back to stack
6. Continue caller execution

## Validation

Sequences are validated on load:

1. **CRC Check:** Footer CRC matches computed CRC
2. **Version Check:** Schema version matches expected version
3. **Bounds Check:** Statement count matches header
4. **Opcode Check:** All opcodes are valid DirectiveId values
5. **Deserialization Check:** All directives deserialize correctly

If validation fails:
- Event logged
- Sequence not loaded
- Sequencer returns to IDLE

## Error Handling

When an error occurs during execution:
1. **Log event** with error code and context
2. **Update telemetry** (sequencesFailed counter)
3. **Notify via seqDoneOut** with EXECUTION_ERROR status
4. **Transition to IDLE** state
5. **Clear sequence** from memory

## Telemetry

The FpySequencer publishes telemetry channels:
- `sequencesSucceeded: U32` - Count of successful sequences
- `sequencesFailed: U32` - Count of failed sequences
- `sequencesCancelled: U32` - Count of cancelled sequences
- `statementsDispatched: U32` - Total statements executed

## Requirements Traceability

The FpySequencer implements 21 requirements (FPY-SEQ-001 through FPY-SEQ-021):
- Branching, conditionals, loops
- Arithmetic and logical operations (64-bit int/float)
- Telemetry and parameter access
- Function calls with arguments and return values
- Scoped variables
- Relative and absolute timing
- Command dispatch
- Exit codes
- Complex data structures (arrays, serializables)
- Runtime flag management
- All 70+ directives

## Thread Safety

- Component is **active** (has own thread and message queue)
- Ports have **priority levels** to ensure critical operations (ping, state machine signals) preempt others
- Port invocations are **serialized** through message queue

## Performance Considerations

1. **Stack size:** Must be >= max TLM/PRM buffer size, <= StackSizeType max
2. **Directive count:** Limited by U16 (65535 statements max)
3. **Argument count:** Limited by U8 (255 arguments max)
4. **Timing accuracy:** Limited by checkTimers rate
5. **Command throughput:** One command response awaited at a time (no command parallelism within sequence)
