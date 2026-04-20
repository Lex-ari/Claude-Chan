---
name: FPP Language Fundamentals
description: Core syntax, types, lexical elements, scoping rules, and fundamental concepts of the F Prime Prime modeling language
type: reference
originSessionId: c7708e45-a599-4300-a457-572b467a90ee
---
# FPP Language Fundamentals

## Overview
F Prime Prime (FPP) is a modeling language for the F Prime flight software framework. FPP provides semantic checking, error reporting, and code generation (C++, JSON) for F Prime models. It offers a cleaner, more succinct syntax compared to writing XML directly.

## Lexical Elements

### Reserved Words
FPP has reserved words that cannot be used as identifiers unless escaped with `$`:
- Primitive types: `bool`, `I8`, `I16`, `I32`, `I64`, `U8`, `U16`, `U32`, `U64`, `F32`, `F64`
- Keywords: `active`, `passive`, `queued`, `component`, `port`, `topology`, `module`, `constant`, `enum`, `struct`, `array`, `type`, `instance`, etc.
- Special: `true`, `false`, `async`, `sync`, `input`, `output`, `command`, `event`, `telemetry`, `param`

### Identifiers
- Must start with letter or underscore
- Can contain letters, digits, underscores
- Can be escaped with `$` prefix to use reserved words as identifiers (e.g., `$time`)

### Comments and Annotations
- **Comments**: Start with `#`, go to end of line, ignored by compiler
- **Pre-annotations**: Start with `@`, appear before element, preserved in generated code
- **Post-annotations**: Start with `@<`, appear after element on same line

### Line Handling
- Explicit line continuation: `\` before newline suppresses it
- Automatic suppression: Symbols `(`, `*`, `+`, `,`, `-`, `->`, `/`, `:`, `;`, `=`, `[`, `{` consume following newlines
- Newlines serve as element separators in sequences

## Type System

### Primitive Types
- **Signed integers**: `I8`, `I16`, `I32`, `I64`
- **Unsigned integers**: `U8`, `U16`, `U32`, `U64`
- **Floating-point**: `F32`, `F64`
- **Boolean**: `bool` (values: `true`, `false`)
- **String**: `string` or `string size N` (N ∈ [1, 2³¹-1])

### User-Defined Types
- **Enum types**: Named enumeration with constant values
- **Struct types**: Structured types with named members
- **Array types**: Fixed-size arrays of elements
- **Abstract types**: Forward-declared types implemented externally
- **Alias types**: Type aliases (like typedef)

### Internal Types (used during type checking)
- **_Integer_**: Represents all integer values without bit width constraint
- **Anonymous array types**: `[n] T`
- **Anonymous struct types**: `{ m1: T1, m2: T2, ... }`

### Type Properties
- **Displayable types**: Types that F Prime ground system can display (primitives, bool, string, enum, arrays/structs of displayable types)
- **Canonical types**: Non-alias types
- **Underlying types**: The canonical type after following alias chain
- **Default values**: Every named type has a default value for initialization

## Scoping and Name Resolution

### Qualified Identifiers
- Simple identifier: `a`
- Qualified: `a.b`, `a.b.c`
- Every definition has a unique qualified name

### Name Groups
Definitions reside in separate name groups to allow same name in different contexts:
1. Component name group
2. Port interface instance name group
3. Port interface name group
4. Port name group
5. State machine name group
6. Type name group
7. Value name group

### Resolution Rules
- Identifiers resolve based on context (which name group)
- Inside module/component: looks for local definition first, then outer scope
- Multiple module definitions with same name merge into single semantic module

## Translation Units and Models

### Translation Units
- Top-level sequence of module members (similar to source files)
- Each unit contains definitions, specifiers, includes

### Models
- Collection of one or more translation units
- Analyzed/translated as a whole
- Location: absolute path of file or current directory (for stdin)

## File Conventions

### .fpp Files
- Main FPP source files
- Directly analyzed and translated
- Can contain complete definitions

### .fppi Files (included files)
- Files meant to be included via `include` specifiers
- Contain fragments of FPP code (constants, types, port lists, etc.)
- Location of definitions is the including file, not the .fppi file

### Include Specifiers
- Syntax: `include "path/to/file.fppi"`
- Path relative to including file's location
- Can appear at top level, in modules, components, topologies, state machines
- Included file must contain complete syntactic units valid for that context

## Key Language Features

### Element Sequences
- Pattern: element, terminator, element, terminator, ..., final-terminator
- Terminating punctuation: typically `;` or `,`
- Newlines act as separators
- Optional trailing terminator before closing brace

### Expressions
- Integer literals: decimal, hex (`0x`), octal (`0o`), binary (`0b`)
- Floating-point literals: standard notation
- String literals: double-quoted
- Boolean literals: `true`, `false`
- Array expressions: `[ e1, e2, e3 ]`
- Struct expressions: `{ m1 = e1, m2 = e2 }`
- Arithmetic operators: `+`, `-`, `*`, `/`
- Dot expressions: `e.id` (member access)
- Sizeof expressions: `sizeof e`

### Evaluation and Type Checking
- Constant expressions evaluated at compile time
- Type conversion rules for numeric types
- Integer promotion, numeric conversion
- Type checking ensures type safety before code generation
