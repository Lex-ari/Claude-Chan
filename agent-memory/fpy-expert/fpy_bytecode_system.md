---
name: Fpy Bytecode System
description: Bytecode format, all 70+ directives, and stack-based execution model
type: reference
---

# Fpy Bytecode System

## Bytecode Architecture

Fpy uses a **stack-based virtual machine** architecture. The FpySequencer maintains:
1. **Program counter** - Index of next statement to execute
2. **Stack** - Byte array for operands, local variables, and function frames
3. **Frame pointer** - Points to current function's local variable area

## File Format

**Schema Version:** 4 (as of current version)

### Binary Structure
```
[Header] - Fixed size structure
[Arguments] - Byte array mapping input args to local vars
[Statements] - Array of (opcode, argBuffer) pairs
[Footer] - CRC32 checksum
```

### Header (`Fpy::Header`)
- `majorVersion: U8` - FSW major version
- `minorVersion: U8` - FSW minor version
- `patchVersion: U8` - FSW patch version
- `schemaVersion: U8` - Bytecode format version (currently 4)
- `argumentCount: U8` - Number of input arguments
- `statementCount: U16` - Number of statements in body
- `bodySize: U32` - Size of statement body in bytes

### Statement Format
Each statement is:
- `opCode: DirectiveId (U8)` - The directive opcode
- `argBuf: Fw.StatementArgBuffer` - Serialized arguments for this directive

### Footer
- `crc: U32` - CRC32 checksum of the entire file

## Stack Model

**Stack Properties:**
- **Size:** Configurable via `Svc::Fpy::MAX_STACK_SIZE` (must be >= max TLM/PRM buffer size)
- **Type:** `StackSizeType` = `U32` (can address up to 4GB stack)
- **Endianness:** Big-endian for all multi-byte values
- **Growth:** Grows upward (higher addresses)

**Stack Operations:**
- `push<T>(val)` - Push value to stack (converts to big-endian)
- `pop<T>()` - Pop value from stack (converts from big-endian)
- `push(bytes, size)` - Push byte array
- `pop(dest, size)` - Pop byte array
- `top()` - Get pointer to top of stack
- `copy(dest, src, size)` - Copy within stack (non-overlapping)
- `move(dest, src, size)` - Move within stack (handles overlap)

**Stack Layout:**
```
High addresses
    ↑
    | Operand stack (grows/shrinks during execution)
    | Local variables for current function
    | (Frame pointer points here)
    | Previous frame's data
    | ...
    | Bottom
Low addresses
```

## Complete Directive Reference (76 Total)

**Location:** `/lib/fpy/src/fpy/bytecode/directives.py` (826 lines)

All directives 9-56 inclusive are **StackOpDirective** subclasses (no arguments, operate on stack).

### Control Flow Directives (3-5, 57, 72-73)

**GOTO (3)** - `GotoDirective`
- Args: `U32 dir_idx` (target statement index)
- Unconditional jump to directive at index (sets `m_runtime.nextStatementIndex = dir_idx`)
- Bounds check: `dir_idx <= statementCount` (allows == for EOF)

**IF (4)** - `IfDirective`
- Args: `U32 false_goto_dir_index`
- Pops `bool` (U8) from stack; if false/zero, jumps to `false_goto_dir_index`; else continues
- Bounds check: `false_goto_dir_index <= statementCount`

**NO_OP (5)** - `NoOpDirective`
- Args: none
- Does nothing; used as placeholder or identity unary op (e.g., unary `+`)

**EXIT (57)** - `ExitDirective`
- Args: none
- Pops `U8 exit_code` from stack
- Terminates sequence immediately (0 = success, nonzero = error)
- Sets `DirectiveErrorCode::EXIT_WITH_ERROR` if exit_code != 0

**CALL (72)** - `CallDirective`
- Args: none
- Pops `U32 target_dir_idx` from stack (function entry point)
- Pushes return address (current_idx + 1) as `U32`
- Pushes current `stack.currentFrameStart` as `U32` (frame header = 8 bytes total)
- Sets `stack.currentFrameStart` to current stack top
- Jumps to target directive

**RETURN (73)** - `ReturnDirective`
- Args: `U32 return_val_size`, `U32 call_args_size`
- Pops return value (if any, `return_val_size` bytes) to temp
- Pops `U32 return_addr` and `U32 prev_frame_start` from frame header
- Restores `stack.currentFrameStart` to prev value
- Discards `call_args_size` bytes (function arguments)
- Pushes return value back (if any)
- Sets PC to return address

### Timing Directives

**WAIT_REL (1)** - Sleep for relative duration
- Stack args: `useconds: U32`, `seconds: U32`

**WAIT_ABS (2)** - Sleep until absolute time
- Stack args: `useconds: U32`, `seconds: U32`, `time_context: U8`, `time_base: U8`

**PUSH_TIME (66)** - Get current time
- Stack result: `Fw.Time` (timeBase, timeContext, seconds, useconds)

### Command Directives

**CONST_CMD (8)** - Dispatch command with constant arguments
- Hardcoded args: `opcode: U32`, `arg_buffer: bytes`

**STACK_CMD (64)** - Dispatch command with stack arguments
- Hardcoded args: `opcode: U32`, `arg_size: U32`
- Stack args: argument bytes (popped in reverse order)

### Data Access Directives

**PUSH_TLM_VAL (6)** - Get telemetry value
- Hardcoded args: `chan_id: U32`
- Stack result: raw telemetry buffer bytes

**PUSH_TLM_VAL_AND_TIME (65)** - Get telemetry value and timestamp
- Hardcoded args: `chan_id: U32`
- Stack result: raw buffer bytes, then `Fw.Time`

**PUSH_PRM (7)** - Get parameter value
- Hardcoded args: `prm_id: U32`
- Stack result: raw parameter buffer bytes

### Stack Operation Directives

All stack ops are opcodes 9-56 inclusive. They operate on values at the top of the stack.

**Boolean Operations:**
- OR (9), AND (10), NOT (27)

**Integer Equality:**
- IEQ (11), INE (12)

**Unsigned Integer Comparison:**
- ULT (13), ULE (14), UGT (15), UGE (16)

**Signed Integer Comparison:**
- SLT (17), SLE (18), SGT (19), SGE (20)

**Float Equality:**
- FEQ (21), FNE (22)

**Float Comparison:**
- FLT (23), FLE (24), FGT (25), FGE (26)

**Type Conversions:**
- FPTOSI (28) - Float to signed int
- FPTOUI (29) - Float to unsigned int
- SITOFP (30) - Signed int to float
- UITOFP (31) - Unsigned int to float

**Integer Arithmetic:**
- ADD (32), SUB (33), MUL (34)
- UDIV (35) - Unsigned division
- SDIV (36) - Signed division
- UMOD (37) - Unsigned modulo
- SMOD (38) - Signed modulo

**Float Arithmetic:**
- FADD (39), FSUB (40), FMUL (41), FDIV (42)
- FPOW (43) - Power
- FLOG (44) - Natural logarithm
- FMOD (45) - Modulo

**Float Bitwidth Conversion:**
- FPEXT (46) - F32 → F64
- FPTRUNC (47) - F64 → F32

**Integer Sign Extension:**
- SIEXT_8_64 (48), SIEXT_16_64 (49), SIEXT_32_64 (50)

**Integer Zero Extension:**
- ZIEXT_8_64 (51), ZIEXT_16_64 (52), ZIEXT_32_64 (53)

**Integer Truncation:**
- ITRUNC_64_8 (54), ITRUNC_64_16 (55), ITRUNC_64_32 (56)

### Memory Directives

**ALLOCATE (58)** - Allocate space on stack
- Hardcoded args: `byte_count: U32`

**PUSH_VAL (61)** - Push constant value
- Hardcoded args: `bytes: byte_array`

**DISCARD (62)** - Pop and discard bytes
- Hardcoded args: `byte_count: U32`

**LOAD_REL (60)** - Load from stack at frame-relative offset
- Hardcoded args: `offset: I32`, `size: U32`

**STORE_REL (71)** - Store to stack at frame-relative offset
- Hardcoded args: `offset: I32`, `size: U32`

**STORE_REL_CONST_OFFSET (59)** - Store to frame-relative with const offset
- Hardcoded args: `offset: I32`, `src_size: U32`

**LOAD_ABS (74)** - Load from absolute stack offset
- Hardcoded args: `offset: U32`, `size: U32`

**STORE_ABS (75)** - Store to absolute stack offset
- Hardcoded args: `offset: U32`, `size: U32`

**STORE_ABS_CONST_OFFSET (76)** - Store to absolute with const offset
- Hardcoded args: `offset: U32`, `src_size: U32`

**PEEK (70)** - Peek at stack without consuming
- Hardcoded args: `offset: I32`, `size: U32`

**MEMCMP (63)** - Compare two memory regions
- Hardcoded args: `size: U32`
- Stack result: `bool` (true if equal)

**GET_FIELD (69)** - Get struct field or array element
- Hardcoded args: `offset: U32`, `size: U32`
- Pops struct/array, pushes field/element

### Flag Directives

**SET_FLAG (67)** - Set sequencer flag
- Stack args: `flag_id: U8`, `value: bool`

**GET_FLAG (68)** - Get sequencer flag value
- Stack args: `flag_id: U8`
- Stack result: `bool`

**Flags:**
- `EXIT_ON_CMD_FAIL (0)` - Exit sequence if command fails

## Error Codes

All errors are `DirectiveErrorCode` enum (U8):
- NO_ERROR (0)
- STMT_OUT_OF_BOUNDS (1)
- TLM_GET_NOT_CONNECTED (2)
- TLM_CHAN_NOT_FOUND (3)
- PRM_GET_NOT_CONNECTED (4)
- PRM_NOT_FOUND (5)
- CMD_SERIALIZE_FAILURE (6)
- EXIT_WITH_ERROR (7)
- STACK_ACCESS_OUT_OF_BOUNDS (8)
- STACK_OVERFLOW (9)
- DOMAIN_ERROR (10)
- FLAG_IDX_OUT_OF_BOUNDS (11)
- ARRAY_OUT_OF_BOUNDS (12)
- ARITHMETIC_OVERFLOW (13)
- ARITHMETIC_UNDERFLOW (14)
- FRAME_START_OUT_OF_BOUNDS (15)
- STACK_UNDERFLOW (16)

## Directive Execution Flow

1. **Fetch:** Load statement at program counter
2. **Decode:** Deserialize directive opcode and arguments
3. **Execute:** Perform directive operation
4. **Update PC:** Increment program counter (or jump for control flow)
5. **Check timing:** If WAIT directive, sleep until ready
6. **Repeat:** Continue to next statement

## Important Implementation Notes

1. **IEEE-754 Required:** Float operations require IEEE-754 compliance
2. **Two's Complement:** Integer operations assume 2's complement
3. **Big Endian:** All multi-byte values on stack are big-endian
4. **Stack Overflow:** Operations validate stack bounds before execution
5. **CRC Validation:** Footer CRC is validated on sequence load
