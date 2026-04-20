---
name: FPP Definitions
description: Complete reference for all FPP definition types - modules, components, ports, types, instances, and topologies
type: reference
originSessionId: c7708e45-a599-4300-a457-572b467a90ee
---
# FPP Definitions

## Module Definitions

**Syntax:** `module Identifier { member-sequence }`

**Purpose:** Provides named scope (like C++ namespace or Java package) that qualifies other definitions.

**Members can include:**
- Component definitions
- Component instance definitions
- Constant definitions
- Other module definitions (nested)
- Port definitions
- Port interface definitions
- State machine definitions
- Type definitions (abstract, alias, array, enum, struct)
- Topology definitions
- Location specifiers
- Include specifiers

**Semantics:**
- Qualifies names of nested definitions
- Multiple module definitions with same name merge semantically
- Definitions inside can be referenced by unqualified name (within module) or qualified name (outside)

## Component Definitions

**Syntax:** `component-kind component Identifier { member-sequence }`

**Component kinds:**
- `active`: Has own thread, processes async commands/ports
- `passive`: No thread, synchronous only
- `queued`: Uses queue but no dedicated thread

**Members can include:**
- Constant definitions
- Type definitions (abstract, alias, array, enum, struct)
- State machine definitions (and instances)
- Command specifiers
- Event specifiers
- Telemetry channel specifiers
- Parameter specifiers
- Port instance specifiers
- Port matching specifiers
- Internal port specifiers
- Container specifiers (data products)
- Record specifiers (data products)
- Interface import specifiers
- Include specifiers

**Key Rules:**
- Passive components: no async ports, no internal ports, no async commands, no state machines
- Active/queued components: must have at least one async port/command/state machine
- Each component may have at most one of each special port kind
- Dictionary specifiers (commands, events, params, telemetry, records, containers) must have distinct names and IDs

**Special Ports Required:**
- Commands require: `command recv`, `command reg`, `command resp`
- Events require: `event`, `text event`, `time get`
- Parameters require: command ports + `param get`, `param set`
- Telemetry requires: `telemetry`, `time get`
- Data products require: `product send`, `time get`, and either `product get` or `product request` (+ `product recv` if request)

## Port Definitions

**Syntax:** `port Identifier [( param-list )] [-> type-name]`

**Purpose:** Defines endpoint for connections between components.

**Elements:**
- **Parameters**: Data carried on port invocation
  - Can be marked `ref` for pass-by-reference (sync) or pass-by-value (async)
- **Return type**: Optional type for synchronous return value

**Example:**
```fpp
port CommandPort(
    opcode: U32
    ref buffer: Fw.ComBuffer
) -> FwOpcodeType
```

## Port Interface Definitions

**Syntax:** `interface Identifier { member-sequence }`

**Purpose:** Groups related port instance specifiers for reuse.

**Members:**
- Port instance specifiers
- Interface import specifiers (compose other interfaces)

**Rules:**
- Each port must have distinct name
- At most one of each special port kind

**Example:**
```fpp
interface CommandInterface {
    command recv port cmdIn
    command reg port cmdRegOut
    command resp port cmdRespOut
}
```

## Component Instance Definitions

**Syntax:** 
```fpp
instance Identifier: QualifiedType
    base id Expression
    [type "ImplType"]
    [at "path/to/impl.hpp"]
    [queue size Expression]
    [stack size Expression]
    [priority Expression]
    [cpu Expression]
    [{ init-specifiers }]
```

**Purpose:** Creates instance of component for use in topology.

**Key attributes:**
- **base id**: Base identifier for component's commands/events/params/telemetry
- **type**: C++ implementation type (defaults to inferred from component name)
- **at**: Path to implementation file
- **queue size**: Required for active/queued components
- **stack size**: Optional for active components
- **priority**: Optional thread priority for active components
- **cpu**: Optional CPU affinity for active components

## Type Definitions

### Abstract Type
**Syntax:** `type Identifier`

Associates name with type without specifying it. Implementation provided externally (e.g., C++ class).

### Alias Type
**Syntax:** `type Identifier = type-name`

Creates type alias (like typedef).

### Array Definition
**Syntax:** `array Identifier = [Expression] type-name [default Expression] [format String]`

Defines fixed-size array type. Size must be compile-time constant > 0.

**Example:**
```fpp
array Matrix3x3 = [9] F64 default 0.0
```

### Enum Definition
**Syntax:** `enum Identifier [: type-name] { constant-sequence } [default Expression]`

Defines enumeration type.
- Default representation type: `I32`
- Can specify explicit representation type (must be primitive integer)
- Constants must have distinct names and values

**Example:**
```fpp
enum Status: U8 {
    OK = 0
    ERROR = 1
    PENDING = 2
} default OK
```

### Struct Definition
**Syntax:** `struct Identifier { member-sequence } [default Expression]`

Defines structure type with named members.

**Member syntax:** `name: [[size]] type-name [format String]`
- Optional `[size]` creates array of that member

**Example:**
```fpp
struct Telemetry {
    timestamp: U64
    value: F64 format "{.3f}"
    samples: [10] F32
}
```

## State Machine Definitions

**Syntax:** `state machine Identifier [{ member-sequence }]`

**Two kinds:**
1. **External**: No body, implementation provided externally
2. **Internal**: Body specifies behavior, code generated

**Members (internal only):**
- Constant definitions
- Type definitions
- Signal definitions
- Action definitions
- Guard definitions
- Choice definitions
- State definitions (can be nested)
- Initial transition specifier (required exactly once)
- Include specifiers

**Key concepts:**
- States can be nested (hierarchical state machine)
- Signals trigger transitions
- Guards control conditional transitions
- Actions execute during transitions
- Initial transition defines starting state
- Generates State enum automatically for leaf states

## Topology Definitions

**Syntax:** `topology Identifier [implements interface-list] { member-sequence }`

**Purpose:** Defines FSW topology - set of component instances and connections between them.

**Members:**
- Connection graph specifiers (named groups of connections)
- Port interface instance specifiers (component/subtopology instances)
- Topology port instance specifiers (topology's own ports)
- Telemetry packet set specifiers
- Include specifiers

**Connection Graphs:**
Named groups capturing different aspects:
```fpp
connections CommandConnections {
    dispatcher.cmdOut -> receiver.cmdIn
}
```

**Graph patterns:** Can use pattern specifiers to auto-generate standard connections:
- Command patterns
- Event patterns
- Telemetry patterns
- Parameter patterns
- Health patterns
- Time patterns

**Port Numbering:**
- Can be explicit: `a.p[0] -> b.q`
- Or automatic (FPP assigns lowest available)
- Port matching: `match p1 with p2` ensures corresponding numbers

**Subtopologies:**
- Reference other topologies as instances
- Connections and instances merged into parent topology
- Topology ports allow external connections

## Constant Definitions

**Syntax:** `constant Identifier = Expression`

Defines compile-time constant. Expression must be evaluatable at compile time.

**Types allowed:**
- Numeric (integer, floating-point)
- Boolean
- String
- Array (of constants)
- Struct (of constants)

## Dictionary Definitions

**Qualifier:** `dictionary` keyword before `constant`, `enum`, `struct`, `array`

Marks definition as dictionary definition - included when generating topology dictionaries.

**Example:**
```fpp
dictionary enum ErrorCode { ... }
```

## Framework Definitions

Special built-in definitions that FPP assumes are provided by F Prime framework:
- `FwSizeStoreType`: Type for storing string lengths
- `FW_FIXED_LENGTH_STRING_SIZE`: Default maximum string length
- Standard port types: `Fw.Cmd`, `Fw.CmdReg`, `Fw.CmdResponse`, etc.
