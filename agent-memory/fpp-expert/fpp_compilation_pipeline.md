---
name: FPP Compilation Pipeline
description: FPP analysis and translation tools, dependency management, code generation workflow, and compilation process
type: reference
originSessionId: c7708e45-a599-4300-a457-572b467a90ee
---
# FPP Compilation Pipeline

## Analysis Process

**Analysis** is the process of checking FPP source models for correctness.

**Steps:**
1. **Lexing**: Convert source text to tokens
2. **Parsing**: Build abstract syntax tree (AST) from tokens
3. **Semantic Analysis**: Type checking, name resolution, constraint validation

**Analysis happens before** any code generation.

## Available Tools

### Core Analysis Tools

**fpp-check**
- Checks FPP models for correctness
- No code generation
- Usage: `fpp-check file1.fpp file2.fpp` or `cat files | fpp-check`
- Options:
  - `-u file`: Write unconnected port instances to file

**fpp-syntax**
- Syntax checking only
- Faster than full analysis

### Translation Tools

**fpp-to-cpp**
- Translates FPP to C++ code
- Usage: `fpp-to-cpp [-i deps.fpp,...] files.fpp`
- Options:
  - `-i file1,file2,...`: Import files for symbols (don't translate)
  - `-p path`: Path prefix for include directives
  - `-n namespace`: Wrap generated code in namespace
- Generates files with `Ac` suffix (e.g., `ComponentAc.hpp`, `ComponentAc.cpp`)

**fpp-to-dict**
- Generates dictionary files (JSON/XML) for ground systems
- Contains commands, events, telemetry, parameters

**fpp-to-layout**
- Generates layout information for struct serialization

### Dependency Management Tools

**fpp-locate-defs**
- Scans FPP files and generates location specifiers
- Usage: `fpp-locate-defs [options] files.fpp`
- Options:
  - `-d dir`: Base directory for relative paths
- Output: Location specifiers showing where definitions are located

**fpp-depend**
- Computes dependencies between FPP files
- Usage: `fpp-depend [options] location-specs.fpp files.fpp`
- Options:
  - `-m file`: Write missing dependencies to file
  - `-i file`: Write included files to file
  - `-d file`: Write direct dependencies (not transitive) to file
  - `-f file`: Write framework dependencies to file
  - `-g file`: Write generated file dependencies to file

**fpp-locate-uses**
- Generates location specifiers for definitions actually used
- Usage: `fpp-locate-uses -i deps.fpp,... files.fpp`
- Options:
  - `-i file1,...`: Import files (definitions available but not analyzed)
  - `-d dir`: Base directory for output paths

### Utility Tools

**fpp-format**
- Formats FPP source code
- Options:
  - `-i`: Expand include specifiers in place

**fpp-filenames**
- Generates expected output filenames for code generation

**fpp-from-xml**
- Converts legacy F Prime XML to FPP

## Typical Workflows

### Check a Simple Model
```bash
fpp-check MyComponent.fpp
```

### Check Model with Dependencies
```bash
# Step 1: Compute dependencies
fpp-depend locations.fpp MyComponent.fpp > deps.txt

# Step 2: Check model with dependencies
fpp-check $(cat deps.txt) MyComponent.fpp
```

### Generate C++ Code
```bash
# For files with dependencies
fpp-to-cpp -i Type1.fpp,Type2.fpp,Port1.fpp MyComponent.fpp

# For standalone files
fpp-to-cpp MyComponent.fpp
```

### Full Build Process (with dependencies)
```bash
# Step 1: Locate all type and port definitions
fpp-locate-defs $(find Types -name '*.fpp') > type-locs.fpp
fpp-locate-defs $(find Ports -name '*.fpp') > port-locs.fpp

# Step 2: Compute dependencies for component
fpp-depend type-locs.fpp port-locs.fpp MyComponent.fpp > deps.txt

# Step 3: Generate C++ with dependencies
fpp-to-cpp -i $(cat deps.txt | tr '\n' ',') MyComponent.fpp
```

## Dependency Management

### Location Specifiers

**Purpose:** Tell analyzer where definitions are located

**Syntax:** `locate [dictionary] kind name at "path"`

**Generation:** Use `fpp-locate-defs` to auto-generate

**File location semantics:**
- For `include` specifiers: location is where file is included, NOT the .fppi file
- Path is relative to location of specifier

### Dependency Resolution

**Process:**
1. Write definitions in various files
2. Run `fpp-locate-defs` on definition files to generate location specifiers
3. Run `fpp-depend` with location specifiers + source files to compute dependencies
4. Use dependency list as imports to analysis/translation tools

**Transitive dependencies:**
- `fpp-depend` computes transitive closure by default
- Use `-d file` option for direct dependencies only (useful for build systems)

**Missing dependencies:**
- Reported via `-m file` option
- Useful for identifying files that need to be generated

### Framework Dependencies

Certain FPP features require F Prime framework modules:
- `Fw_Comp`: Passive components
- `Fw_CompQueued`: Queued or active components  
- `Os`: Active/queued components or guarded ports

Use `fpp-depend -f file` to identify required framework modules.

## Code Generation

### C++ File Naming

| FPP Definition | Generated Files |
|----------------|-----------------|
| Constants | `FppConstantsAc.{hpp,cpp}` |
| Array A (top-level) | `AArrayAc.{hpp,cpp}` |
| Array A in component C | `C_AArrayAc.{hpp,cpp}` |
| Array A in state machine M | `M_AArrayAc.{hpp,cpp}` |
| Enum E (top-level) | `EEnumAc.{hpp,cpp}` |
| Enum E in component C | `C_EEnumAc.{hpp,cpp}` |
| Struct S (top-level) | `SSerializableAc.{hpp,cpp}` |
| Struct S in component C | `C_SSerializableAc.{hpp,cpp}` |
| Alias type T (top-level) | `TAliasAc.{hpp,h,cpp}` |
| Alias type T in component C | `C_TAliasAc.{hpp,h,cpp}` |
| Port P | `PPortAc.{hpp,cpp}` |
| Component C | `CComponentAc.{hpp,cpp}` |
| State machine M (top-level) | `MStateMachineAc.{hpp,cpp}` |
| State machine M in component C | `C_MStateMachineAc.{hpp,cpp}` |
| Topology T | `TTopologyAc.{hpp,cpp}` |

**Note:** `.h` files only generated for C-compatible alias types

### C++ Code Structure

**Namespaces:** Correspond to FPP modules
```fpp
module M {
  struct S { x: U32 }
}
```
Generates: `M::S` class

**Constants:** 
- Integer constants → enum constants
- Floating-point → `const` variables
- Boolean → `const bool` variables
- String → `const char* const` variables

**Components:**
- Generate base class `ComponentNameComponentAc`
- User implements derived class `ComponentName` (manually written)

**Ports:**
- Generate port base classes
- Input ports: provide handler signature
- Output ports: provide invocation interface

### Include Path Management

Generated code includes dependencies using paths derived from:
1. Location specifiers for dependencies
2. `-p` path prefix option (optional)

**Example:**
If `TypeA` at `/repo/Types/TypeA.fpp` and using `-p /repo`, generated include is:
```cpp
#include "Types/TypeAAc.hpp"
```

## Build Integration

### CMake Integration (F Prime)

F Prime's CMake system integrates FPP:
1. Discovers `.fpp` files in module
2. Runs `fpp-locate-defs` for framework types/ports
3. Runs `fpp-depend` to compute dependencies
4. Runs `fpp-to-cpp` to generate code
5. Compiles generated C++ alongside hand-written implementation

### Manual Build Process

For standalone use:
```bash
# 1. Generate location specifiers for available definitions
find Framework -name '*.fpp' | xargs fpp-locate-defs > framework-locs.fpp

# 2. For each module/component:
# 2a. Compute dependencies
fpp-depend framework-locs.fpp MyModule/*.fpp > MyModule/deps.txt

# 2b. Generate C++
fpp-to-cpp -i $(cat MyModule/deps.txt | tr '\n' ',') MyModule/*.fpp

# 2c. Compile C++ (example with g++)
g++ -c MyModule/*Ac.cpp MyModule/*.cpp -I/path/to/fprime
```

## Path Handling

**Relative paths:** Resolved relative to current directory at runtime

**Symbolic links:** JVM resolves symlinks, which may cause unexpected path behavior
- Use `-p` option with absolute paths to control include generation
- Ensure consistent paths when presenting same file multiple times

**Best practice:** Use absolute paths or carefully managed relative paths

## Error Reporting

FPP tools provide detailed error messages:
- File location (file:line.column)
- Error description
- Context (surrounding code)

**Exit codes:**
- 0: Success
- Non-zero: Error occurred

## Testing

**Scala unit tests:** `./fpp-sbt test` in compiler directory

**Command-line tests:** `./test` after `./install`

## Installation

**Requirements:**
- Unix environment (Linux, macOS, WSL)
- Java 11 JDK
- Scala sbt (Simple Build Tool)

**Installation:** `./install [dir]` from compiler directory

**Tools installed:**
- All FPP command-line tools listed above
- Shell scripts that invoke JVM with appropriate classpath

**Native binaries:** Can build using GraalVM's `native-image` tool (see `./release` script)
