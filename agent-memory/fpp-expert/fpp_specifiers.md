---
name: FPP Specifiers
description: Command, event, telemetry, parameter, port instance, and other specifiers used in FPP component and topology definitions
type: reference
originSessionId: c7708e45-a599-4300-a457-572b467a90ee
---
# FPP Specifiers

Specifiers are syntactic elements that appear within definitions (primarily components and topologies) to specify properties and behaviors.

## Command Specifiers

**Syntax:** `command-kind command Identifier [(param-list)] [opcode Expr] [priority Expr] [queue-full-behavior]`

**Command kinds:**
- `sync`: Synchronous, blocks caller until complete
- `async`: Asynchronous, queued for execution
- `guarded`: Synchronous but uses mutex lock

**Elements:**
- **Parameters**: Must be displayable types, no `ref` keyword allowed
- **Opcode**: Numeric command identifier (default: 0 for first, previous+1 for rest)
- **Priority**: Queue priority (async only)
- **Queue-full behavior**: `assert` (default) or `drop` (async only)

**Example:**
```fpp
async command TAKE_IMAGE(
    exposure: F32 @< Exposure time in seconds
    filter: U8 @< Filter number
) opcode 0x10 priority 10 drop
```

## Event Specifiers

**Syntax:** `event Identifier [(param-list)] severity severity-level [id Expr] format String [throttle throttle-spec]`

**Severity levels:**
- `activity high` / `activity low`
- `command`
- `diagnostic`
- `fatal`
- `warning high` / `warning low`

**Throttling:**
- `throttle N`: Emit at most N instances before requiring reset
- `throttle N every { seconds = S, useconds = U }`: Auto-reset after time period

**Format string:** Arguments are event parameter values

**Example:**
```fpp
event IMAGE_CAPTURED(
    timestamp: U64 @< Image timestamp
    size: U32 @< Image size in bytes
) severity activity low \
  id 0x20 \
  format "Image captured at {} with size {} bytes" \
  throttle 100 every { seconds = 60 }
```

## Telemetry Channel Specifiers

**Syntax:** `telemetry Identifier: type-name [id Expr] [update update-mode] [format String] [low { limits }] [high { limits }]`

**Update modes:**
- `always`: Emit every update
- `on change`: Emit only when value changes

**Limits:** `red`, `orange`, `yellow` thresholds for ground monitoring

**Type:** Must be displayable type

**Example:**
```fpp
telemetry Temperature: F32 \
  id 0x30 \
  update on change \
  format "{.2f}" \
  low { red -40.0, orange -30.0, yellow -20.0 } \
  high { yellow 80.0, orange 90.0, red 100.0 }
```

## Parameter Specifiers

**Syntax:** `param Identifier: type-name [default Expr] [id Expr] [set opcode Expr] [save opcode Expr]`

**Purpose:** Configurable component parameters persisted across runs.

**Elements:**
- **Type**: Must be displayable type
- **Default**: Default parameter value
- **ID**: Numeric parameter identifier
- **Set opcode**: Command opcode for setting parameter
- **Save opcode**: Command opcode for saving parameter

## Port Instance Specifiers

**Syntax:** `[general] [kind] [special-kind] port Identifier: [size] type-name [priority Expr] [queue-full]`

**Port directions:**
- `input`: Receives data
- `output`: Sends data

**Port kinds:**
- `sync`: Synchronous call
- `async`: Asynchronous, queued
- `guarded`: Synchronous with mutex

**Size:** `[N]` creates array of N port instances

**Queue-full behavior:** `assert` (default) or `drop` (async only)

**Special port kinds:**
- `command recv`: Receives commands
- `command reg`: Registers commands
- `command resp`: Sends command responses
- `event`: Emits events
- `text event`: Emits text events
- `time get`: Gets current time
- `telemetry`: Emits telemetry
- `param get`: Gets parameter values
- `param set`: Sets parameter values
- `product send`: Sends data products
- `product get`: Gets data product buffers
- `product request`: Requests data product buffers
- `product recv`: Receives data product requests

**Examples:**
```fpp
async input port schedIn: Svc.Sched
output port cmdOut: [10] Fw.Cmd
command recv port cmdIn
sync input port run: Svc.Cycle priority 10
```

## Internal Port Specifiers

**Syntax:** `internal port Identifier [(param-list)] [priority Expr] [queue-full]`

**Purpose:** Component can invoke itself asynchronously (async "to self").

**Example:**
```fpp
internal port processData(
    buffer: Fw.Buffer
) priority 5
```

## Port Matching Specifiers

**Syntax:** `match port1 with port2`

**Purpose:** Ensures corresponding port numbers between matched port arrays.

**Example:**
```fpp
match reqIn with respOut
```
Ensures `reqIn[0]` corresponds to `respOut[0]`, etc.

## Interface Import Specifiers

**Syntax:** `import QualifiedInterfaceName`

**Purpose:** Imports port instances from a port interface definition.

**Example:**
```fpp
import CommandInterface
```

## Connection Graph Specifiers

**Syntax:** `connections Identifier { connection-sequence }`

**Connection syntax:** `source-endpoint -> dest-endpoint [unmatched]`

**Endpoint syntax:** `instance.port[[number]]`

**Pattern specifiers:** Generate standard connections automatically
- `command`
- `event`
- `telemetry`
- `param`
- `health`
- `time`
- `text event`

**Example:**
```fpp
connections Commanding {
    dispatcher.cmdOut[0] -> receiver.cmdIn
    receiver.cmdResponseOut -> dispatcher.cmdResponseIn
}

connections Downlink {
    command
    event
    telemetry
}
```

## Topology Port Instance Specifiers

**Syntax:** `port Identifier = instance.port`

**Purpose:** Exposes component port as topology port for external connections.

**Example:**
```fpp
topology SubTopology {
    instance comp: MyComponent base id 0x100
    port externalCmd = comp.cmdIn
}
```

## Location Specifiers

**Syntax:** `locate [dictionary] definition-kind QualifiedName at "path"`

**Definition kinds:** `constant`, `type`, `component`, `port`, `instance`, `interface`, `state machine`, `topology`

**Purpose:** Tells analyzer where to find definitions (used for dependency management).

**Note:** Usually auto-generated by `fpp-locate-defs`, not written by hand.

**Example:**
```fpp
locate type MyType at "types/MyType.fpp"
locate constant MAX_SIZE at "constants/Limits.fpp"
locate dictionary enum ErrorCode at "enums/Errors.fpp"
```

## Include Specifiers

**Syntax:** `include "path/to/file.fppi"`

**Purpose:** Includes FPP code from another file at this location.

**Valid contexts:**
- Top level (translation unit)
- Inside modules
- Inside components
- Inside topologies
- Inside state machines

**Path:** Relative to including file's location

## Init Specifiers

**Syntax:** Inside component instance definition `{ init-specifiers }`

**Purpose:** Governs C++ code generation for component instance initialization.

**Specifiers:**
- `phase Expr`: Initialization phase
- `code String`: Custom initialization code

## Container Specifiers (Data Products)

**Syntax:** `product container Identifier [id Expr] [default priority Expr]`

**Purpose:** Specifies data product container in component.

**Example:**
```fpp
product container ImageContainer id 0x40
```

## Record Specifiers (Data Products)

**Syntax:** `product record Identifier: type-name [id Expr] [array]`

**Purpose:** Specifies data product record in component.

**Array qualifier:** Makes it an array record

**Example:**
```fpp
product record ImageRecord: ImageData id 0x41 array
```

## Telemetry Packet Set Specifiers

**Syntax:** Inside topology definition

**Purpose:** Assigns telemetry channels to packets for downlink.

**Example:**
```fpp
packet set id 1 {
    packet 1 { channel1, channel2 }
    packet 2 { channel3, channel4 }
}
```

## Format Strings

Used in commands, events, telemetry, types to specify display formatting.

**Syntax:** Subset of Python format strings
- `{}`: Default formatting
- `{.3f}`: Floating-point with 3 decimal places
- `{x}`: Hexadecimal
- `{d}`: Decimal

**Arguments:** Correspond to parameters/values being formatted
