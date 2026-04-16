---
name: Fpy Key Files
description: Important file locations for compiler and sequencer implementation
type: reference
---

# Fpy System Key Files

## Fpy Compiler (Python)

**Base Directory:** `/lib/fpy/src/fpy/`

### Core Compiler Files

- **`compiler.py`** - Main compilation orchestrator, runs all passes
  - Function: `compile()` - Entry point for compilation
  - Initializes parser, runs semantic analysis, desugaring, codegen

- **`main.py`** - CLI entry point for `fprime-fpyc` command
  - Argument parsing
  - Dictionary loading
  - Output file handling

- **`grammar.lark`** - Lark LALR grammar defining Fpy syntax
  - Python-like indentation-sensitive syntax
  - Expression precedence
  - Statement and block structure

- **`syntax.py`** - AST node definitions and parse tree transformer
  - `AstBlock` and other AST node types
  - `FpyTransformer` - Converts Lark parse tree to AST
  - `PythonIndenter` - Handles indentation-based blocks

### Semantic Analysis

- **`semantics.py`** - All semantic analysis passes (15+ passes)
  - Type checking
  - Name resolution
  - Const expression evaluation
  - Use-before-define checking
  - Return statement validation

- **`types.py`** - Type system implementation
  - `FpyType` and `FpyValue` classes
  - Type hierarchy and conversions
  - Built-in types (I8-I64, U8-U64, F32, F64, bool, Fw.Time, etc.)

- **`state.py`** - Compiler state management
  - `CompileState` - Global compilation state
  - Symbol tables and scopes
  - Variable and function tracking

### Code Generation

- **`desugaring.py`** - AST transformations for syntactic sugar
  - `DesugarDefaultArgs`
  - `DesugarForLoops`
  - `DesugarCheckStatements`
  - `DesugarTimeOperators`

- **`codegen.py`** - IR generation and optimization
  - `GenerateModule` - Module-level code generation
  - `GenerateFunctions` - Function code generation
  - `CalculateFrameSizes` - Stack frame size computation
  - `ResolveLabels` - Label to statement index resolution

- **`ir.py`** - Intermediate representation definitions
  - IR data structures (minimal, delegates to bytecode)

### Bytecode

- **`bytecode/` directory** - Bytecode definitions and serialization
  - `directives.py` - All 70+ directive definitions
  - Serialization to binary format
  - Directive argument encoding

### Support

- **`dictionary.py`** - F Prime dictionary loading
  - JSON dictionary parsing
  - Command/telemetry/parameter lookup
  - Type resolution from dictionary

- **`error.py`** - Error handling and reporting
  - `CompileError` exception
  - Source location tracking
  - Pretty error formatting

- **`macros.py`** - Built-in macro definitions
  - `exit` macro
  - `assert` macro
  - Macro expansion logic

- **`visitors.py`** - AST visitor base classes
  - `Visitor` - Generic AST traversal
  - Used by semantic passes

- **`model.py`** - Python model of FpySequencer runtime
  - Used for testing
  - Simulates bytecode execution

- **`test_helpers.py`** - Testing utilities

### Built-in Library

- **`builtin/time.fpy`** - Built-in time manipulation functions
  - `time_cmp()` - Compare times
  - `time_add()` - Add interval to time
  - `time_sub()` - Subtract times
  - Auto-included in all sequences

## FpySequencer Component (C++)

**Base Directory:** `/lib/fprime/Svc/FpySequencer/`

### Core Component Files

- **`FpySequencer.hpp`** - Component header
  - Class definition
  - Stack implementation
  - DirectiveUnion for directive storage
  - Private member variables and methods

- **`FpySequencer.cpp`** - Main component implementation
  - Constructor/destructor
  - Port handler registration

- **`FpySequencer.fpp`** - FPP component definition
  - Port definitions (input/output)
  - Enum definitions (BlockState, GoalState, FileReadStage)
  - Component topology specification

### State Machine

- **`FpySequencerStateMachine.cpp`** - State machine implementation
  - State entry/exit actions
  - Signal handlers
  - State transitions

- **`FpySequencerStateMachine.fppi`** - FPP state machine definition
  - State hierarchy
  - Transition conditions
  - Actions

### Runtime Execution

- **`FpySequencerRunState.cpp`** - Runtime execution logic
  - `dispatchStatement()` - Fetch-decode-execute cycle
  - `deserializeDirective()` - Directive deserialization
  - Program counter management

- **`FpySequencerDirectives.cpp`** - Directive execution handlers
  - Implementation for all 70+ directives
  - Stack operations
  - Command dispatch
  - Telemetry/parameter access

- **`FpySequencerStack.cpp`** - Stack implementation
  - Push/pop operations
  - Endianness conversion
  - Bounds checking
  - Memory copy/move

### Validation

- **`FpySequencerValidationState.cpp`** - Sequence validation
  - CRC checking
  - Version validation
  - Bounds checking

### Type Definitions

- **`FpySequencerTypes.fpp`** - Type and constant definitions
  - `DirectiveId` enum (all 76 opcodes)
  - `DirectiveErrorCode` enum
  - `FlagId` enum
  - `Header`, `Footer`, `Statement`, `Sequence` structs
  - Constants (SCHEMA_VERSION, FLAG_COUNT, etc.)

- **`FpySequencerDirectives.fppi`** - Directive structure definitions
  - FPP definitions for each directive's arguments
  - Serializable types for each directive

### Commands and Telemetry

- **`FpySequencerCommands.fppi`** - Command definitions
  - RUN, VALIDATE, RUN_VALIDATED, CANCEL
  - Debugging commands (SET_BREAKPOINT, BREAK, CONTINUE, etc.)
  - SET_FLAG

- **`FpySequencerEvents.fppi`** - Event definitions
  - Sequence lifecycle events
  - Error events
  - Debug events

- **`FpySequencerTelemetry.fppi`** - Telemetry channel definitions
  - Success/failure counters
  - Current sequence state

- **`FpySequencerParams.fppi`** - Parameter definitions
  - Flag default values

### Documentation

- **`docs/sdd.md`** - Software Design Document
  - State machine diagram
  - Requirements
  - Component overview

- **`docs/directives.md`** - Complete directive reference
  - All 70+ directives documented
  - Argument types (hardcoded vs stack)
  - Stack result types
  - Requirements traceability

### Build

- **`CMakeLists.txt`** - CMake build configuration

### Tests

- **`test/` directory** - Unit and integration tests

## Framework Support Files

**Base Directory:** `/lib/fprime/Fw/Fpy/`

- **`StatementArgBuffer.fpp`** - Argument buffer type definition
- **`StatementArgBuffer.hpp/cpp`** - Argument buffer implementation

## Other Important Locations

### F Prime Core
- `/lib/fprime/Fw/` - Framework types used by Fpy (Time, Com, etc.)
- `/lib/fprime/Svc/CmdSequencer/` - Traditional sequencer (for comparison)
- `/lib/fprime/docs/` - F Prime documentation

### Test/Example Code
- `/lib/fpy/test/` - Fpy compiler test suite
- `/lib/fpy/test/fpy/` - Test .fpy sequences

## Configuration Files

- `/lib/fpy/pyproject.toml` - Python package configuration
- `/lib/fpy/setup.py` - Python package setup
- Project `settings.ini` - F Prime project settings
