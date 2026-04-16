---
name: Fpy Compiler Pipeline
description: Complete compilation pipeline from .fpy source to bytecode
type: reference
---

# Fpy Compilation Pipeline

## Overview

The Fpy compiler transforms `.fpy` source files into binary bytecode files (`.bin`) that can be executed by the FpySequencer component in F Prime flight software.

**Location:** `/lib/fpy/src/fpy/`

## Compilation Phases

### 1. Parsing (`grammar.lark`, `syntax.py`)
**Location:** `/lib/fpy/src/fpy/`

- **Input:** `.fpy` source text
- **Parser:** Lark LALR parser with `PythonIndenter` postlexer (cached at module level)
- **Grammar:** `grammar.lark` - 235 lines defining Python-like syntax
- **Transformer:** `FpyTransformer` in `syntax.py` converts parse tree to AST
- **Output:** Abstract Syntax Tree (AST) with `AstBlock` nodes

**Entry:** `compiler.py::text_to_ast()` lines 115-155

**Builtin Library:** Automatically prepends `/lib/fpy/src/fpy/builtin/time.fpy` functions to AST (lines 86-112, 466-467 in compiler.py)

**AST Nodes (syntax.py, 571 lines):**
- Control: `AstIf`, `AstFor`, `AstWhile`, `AstCheck`, `AstDef`
- Expressions: `AstBinaryOp`, `AstUnaryOp`, `AstFuncCall`, `AstGetAttr`, `AstIndexExpr`, `AstRange`, `AstAnonStruct`, `AstAnonArray`
- Statements: `AstAssign`, `AstReturn`, `AstBreak`, `AstContinue`, `AstPass`, `AstAssert`
- Literals: `AstNumber`, `AstString`, `AstBoolean`, `AstIdent`

### 2. Pre-Semantic Desugaring
**Location:** Lines 472-474 in `compiler.py`

Single pass before semantic analysis:
- **`DesugarCheckStatements`** - Transforms `check ... persist ... timeout` polling statements into while/if constructs (must run before semantic analysis creates scopes)

### 3. Semantic Analysis (`semantics.py` - 2563 lines)

**Location:** Lines 476-505 in `compiler.py` - 14 sequential passes

**Pass 1: `AssignIds`**
- Assigns unique `node.id` to every AST node for dict indexing (state.next_node_id)

**Pass 2: `CreateScopes`**
- Creates `SymbolTable` hierarchy with parent pointers for lexical scoping
- Function bodies get `scope.in_function = True`
- For loops create separate body scope containing loop variable
- Stores mapping in `state.enclosing_value_scope[node]`

**Pass 3: `CreateVariablesAndFuncs`**
- Two-phase visitor: Phase 1 processes all non-function nodes (registers globals/for-loop vars), Phase 2 descends into function bodies
- Allows functions to reference globals declared later in source
- Creates `VariableSymbol(name, type_ann, node, is_global)` on `AstAssign` with type annotation
- Adds symbols to appropriate scope in symbol table

**Pass 4: `CheckBreakAndContinueInLoop`**
- Validates `break`/`continue` only in loops, stores which loop they belong to

**Pass 5: `CheckReturnInFunc`**
- Ensures `return` only appears inside functions

**Pass 6: `ResolveQualifiedNames`**
- Resolves dotted names (`Fw.Time`, `CdhCore.cmdDisp.CMD_NO_OP`) using three global scopes
- Three global scopes built from dictionary: `type_scope`, `callable_scope`, `values_scope`
- Stores resolved symbol in `state.resolved_symbols[node]`

**Pass 7: `UpdateTypesAndFuncs`**
- Resolves type annotations to actual `FpyType` objects
- Handles function signatures and variable declarations

**Pass 8: `CheckUseBeforeDefine`**
- Prevents variables being used before declaration (allows forward refs to globals from functions)

**Pass 9: `PickTypesAndResolveFields`** (MOST COMPLEX - ~800 lines in semantics.py)
- Bottom-up type inference for all expressions
- Resolves struct member access (`.member`) and array indexing (`[index]`)
- Determines operator intermediate types (e.g., `/` always F64, `+` promotes to widest operand type)
- Applies implicit type coercions (int→float, narrow→wide)
- Validates field accesses and array bounds (for const indices)
- Stores result in `state.contextual_types[node]: FpyType`

**Pass 10: `CalculateDefaultArgConstValues`**
- Evaluates default argument expressions at compile time (must be const: literals, enum constants, type ctors)
- Must precede Pass 11 for forward-referenced functions

**Pass 11: `CalculateConstExprValues`**
- Constant-folds expressions (literals, math on literals, enum values, type constructors with const args)
- Stores `FpyValue` in `state.const_expr_values[node]`
- Used for array bounds checks and optimization (const expressions become PUSH_VAL directives)

**Pass 12: `CheckFunctionReturns`**
- Ensures all control-flow paths in functions with return types end with `return`

**Pass 13: `CheckConstArrayAccesses`**
- Array index bounds checking when index is compile-time constant

**Pass 14: `WarnRangesAreNotEmpty`**
- Warns if for-loop ranges are provably empty (e.g., `for i in 5..3`)

**Output:** Typed and validated AST with complete symbol tables and type information

### 4. Post-Semantic Desugaring (`desugaring.py` - 780 lines)

**Location:** Lines 506-513 in `compiler.py` - 3 sequential passes

**Pass 1: `DesugarDefaultArgs`**
- Fills in missing function arguments with default values at call sites (generates code to evaluate defaults)

**Pass 2: `DesugarTimeOperators`**
- Rewrites `Fw.Time` arithmetic (`t1 + interval`, `t2 - t1`, comparisons) into builtin function calls
- E.g., `t1 + interval` → `time_add(t1, interval)` call to `builtin/time.fpy`

**Pass 3: `DesugarForLoops`**
- Transforms `for i in lower..upper:` into:
  ```python
  _lower = lower
  _upper = upper
  i = _lower
  while i < _upper:
      <body>
      i = i + 1
  ```
- Loop variable becomes `I64` type, reuses existing variable if name and type match

**Output:** Simplified AST with only core language features

### 5. Code Generation (`codegen.py` - 1171 lines)

**Location:** Lines 514-548 in `compiler.py`

**Pass 1: `CalculateFrameSizes`** (lines 151-192 in codegen.py)
- Assigns stack frame offsets to all variables (globals in root frame, locals in function frames)
- Function arguments get negative offsets (before frame header: -STACK_FRAME_HEADER_SIZE - arg_size)
- Local variables get sequential positive offsets starting at 0
- Stores `sym.frame_offset: int` for each `VariableSymbol`
- Stores `state.frame_sizes[node]: int` total size for each frame (root and function bodies)

**Pass 2: `CollectUsedFunctions`** (lines 137-148)
- Visits all `AstFuncCall` nodes, marks called functions as used (transitive closure)
- Stores in `state.used_funcs: set[AstDef]`
- Only used functions get code generated (dead code elimination)

**Pass 3: `GenerateFunctionEntryPoints`** (lines 195-201)
- Creates `IrLabel(node, "entry")` for each used function's entry point
- Stores in `state.func_entry_labels[AstDef]: IrLabel`

**Pass 4: `GenerateFunctions`** (lines 204-223)
- For each used function:
  1. Emits entry label
  2. Emits `AllocateDirective(lvar_array_size)` for local variables
  3. Delegates to `GenerateFunctionBody` emitter for function body code
  4. Adds implicit `ReturnDirective(0, arg_bytes)` if function doesn't return value and doesn't explicitly return
- Stores in `state.generated_funcs[AstDef]: list[Directive | Ir]`

**Pass 5: `GenerateModule`** (lines 226+ in codegen.py, invoked line 548 in compiler.py)
- Emits code for module-level (global) variables: `AllocateDirective` for global frame
- Emits code for main sequence body using `GenerateFunctionBody` emitter
- Concatenates all function code from `state.generated_funcs`
- Returns complete IR: `list[Directive | Ir]` (mix of concrete directives and IR labels/gotos)

**Key Emitter: `GenerateFunctionBody`** (lines 226-1100+ in codegen.py)
- Recursive visitor that emits directives for each AST node type
- Handles expressions (push results to stack), statements (manipulate stack/control flow)
- Tracks stack depth, applies type conversions
- Generates stack operations for arithmetic/comparisons
- Emits command directives for function calls, telemetry/param access
- Creates labels and jumps for control flow (if/while/for)

**Output:** List of `Directive` and `Ir` objects (labels, gotos, ifs not yet resolved to concrete directives)

### 6. IR Resolution and Validation

**Location:** Lines 526-554 in `compiler.py` - 2 sequential IR passes

**Pass 1: `ResolveLabels`** (in codegen.py)
- Converts `IrLabel`, `IrGoto`, `IrIf`, `IrPushLabelOffset` into concrete directives
- Assigns directive indices to labels (tracks position in directive list)
- Replaces `IrGoto(label)` with `GotoDirective(dir_idx)`
- Replaces `IrIf(label)` with `IfDirective(dir_idx)`
- Replaces `IrPushLabelOffset(label)` with `PushValDirective(U32_bytes(dir_idx))`

**Pass 2: `FinalChecks`** (in codegen.py)
- Validates all IR has been converted to concrete `Directive` objects (no IrLabel/IrGoto remaining)
- Checks directive count <= `state.max_directives_count` (from FPrime constant, default 65535)
- Checks each directive size <= `state.max_directive_size` (from FPrime constant, default ~16KB)
- Returns `BackendError` if limits exceeded

**Output:** Final `list[Directive]` ready for serialization

### 7. Bytecode Serialization (`bytecode/assembler.py`)

**Location:** `/lib/fpy/src/fpy/bytecode/assembler.py`

Serializes directive list into binary format (invoked from `main.py::compile_main()` line 122):

**Serialization:** `serialize_directives(directives) -> (bytes, crc)`
- **Header:**
  - `U8 majorVersion`, `U8 minorVersion`, `U8 patchVersion` (language version)
  - `U8 schemaVersion` (bytecode format version, currently 4)
  - `U32 statementCount` (number of directives)
- **Body:** Each directive serialized as:
  - `U8 opcode` (DirectiveId enum value)
  - `U16 arg_size` (size of args in bytes)
  - `args...` (serialized arguments, big-endian)
- **Footer:**
  - `U32 crc` (CRC-32 checksum of header + body, initial value 0xFFFFFFFF)

**All multi-byte values are big-endian** (network byte order)

**Directive Serialization:**
- Each directive class has `_FIELD_TYPES: dict[str, FpyType]` mapping field names to Fpy types
- `Directive.serialize()` method calls `FpyValue(type, value).serialize()` for each field
- `FpyValue.serialize()` in `types.py` handles primitives, structs (recursive), arrays, enums

**Output:** Binary `.bin` file ready for FpySequencer

## Key Compiler Files

| File | Purpose |
|------|---------|
| `compiler.py` | Main compilation orchestrator, runs all passes |
| `grammar.lark` | Lark grammar defining Fpy syntax |
| `syntax.py` | AST node definitions and parse tree transformer |
| `semantics.py` | Type checking, name resolution, validation passes |
| `desugaring.py` | AST transformations for syntactic sugar |
| `codegen.py` | IR generation from AST |
| `types.py` | Type system definitions |
| `state.py` | Compiler state, symbol tables, scopes |
| `dictionary.py` | F Prime dictionary loading and parsing |
| `error.py` | Error handling and reporting |
| `macros.py` | Built-in macros (`exit`, `assert`, etc.) |
| `bytecode/` | Bytecode directive definitions and serialization |

## Dictionary Integration

The compiler loads the F Prime dictionary (JSON format) to:
- Resolve command names to opcodes
- Validate command argument types
- Access telemetry channel IDs and types
- Access parameter IDs and types
- Use project-defined struct/array/enum types

**Dictionary Path:** Passed via `--dictionary` flag to `fprime-fpyc`

## Built-in Library

The compiler automatically includes built-in functions from:
- `/lib/fpy/src/fpy/builtin/time.fpy`

This provides functions like `time_cmp`, `time_add`, `time_sub`, etc. for working with `Fw.Time` and `Fw.TimeInterval` types.

## Compilation Entry Point

**Command:** `fprime-fpyc <file.fpy> --dictionary <dict.json>`

**Main function:** `/lib/fpy/src/fpy/main.py`

**Compiler function:** `/lib/fpy/src/fpy/compiler.py` - `compile()` function

## Output Formats

1. **Binary (`.bin`)** - Default, for FpySequencer execution
2. **Human-readable (`.fpybc`)** - With `--bytecode` flag, for debugging

## Tools

- **`fprime-fpyc`** - Compiler
- **`fprime-fpy-model`** - Python model of FpySequencer for testing
- **`fprime-fpy-asm`** - Assembles `.fpybc` to `.bin`
- **`fprime-fpy-disasm`** - Disassembles `.bin` to `.fpybc`
