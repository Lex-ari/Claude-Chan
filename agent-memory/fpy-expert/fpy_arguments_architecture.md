---
name: Fpy Arguments Architecture
description: How runtime arguments work in Fpy sequences - stack layout, frame pointers, and LOAD_REL access patterns
type: user
---

# Fpy Sequence Arguments Architecture

## RUN_ARGS Command Flow
When RUN_ARGS executes, arguments are pushed to the stack BEFORE the sequence begins executing via the `pushArgsToStack` action in the state machine's RUNNING state entry.

Location: `/lib/fprime/Svc/FpySequencer/FpySequencerStateMachine.cpp` lines 261-284

## Stack Frame Layout
The Fpy runtime maintains a frame pointer (`stack.currentFrameStart`) that points to the start of the current function's local variables.

When a function/sequence is called via CALL directive:
1. Arguments are pushed to stack first
2. Target address is pushed
3. CALL instruction:
   - Pops target address
   - Pushes return address (4 bytes, U32)
   - Pushes saved frame pointer (sizeof(StackSizeType) bytes)
   - Sets new `currentFrameStart = stack.size` (after the frame header)

Stack layout after CALL:
```
[... caller's frame ...]
[argument N]
[argument 1]
[return_addr (4 bytes)]
[saved_frame_ptr (sizeof(StackSizeType))]
<-- currentFrameStart points here
[local variable space allocated by ALLOCATE]
```

## Accessing Arguments with LOAD_REL
LOAD_REL uses `lvarOffset` relative to `currentFrameStart`:
- Positive offsets: access local variables (allocated via ALLOCATE)
- Negative offsets: access arguments passed by caller

To access arguments, use:
```
lvarOffset = -(STACK_FRAME_HEADER_SIZE + offset_into_args)
where STACK_FRAME_HEADER_SIZE = sizeof(U32) + sizeof(StackSizeType) = 4 + 2 = 6 bytes (or 8 on 64-bit)
```

Location: `/lib/fpy/src/fpy/bytecode/SPEC.md` lines 766-792, 968-1027

## Key Insight for RUN_ARGS
**RUN_ARGS is for top-level sequences, not function calls!**

For RUN_ARGS:
- Arguments are pushed directly to the empty stack
- No CALL instruction precedes execution
- Stack starts with `currentFrameStart = 0`
- The sequence can:
  1. Use ALLOCATE to reserve space for local variables AFTER the arguments
  2. Access arguments with LOAD_REL using POSITIVE offsets (0 to arg_size-1)
  3. OR access them directly if no ALLOCATE is used

**Critical Difference**: 
- CALL: Arguments accessed via negative LOAD_REL offsets (below frame pointer)
- RUN_ARGS: Arguments accessible via positive LOAD_REL offsets (if frame is positioned after them) OR by just leaving them on stack
