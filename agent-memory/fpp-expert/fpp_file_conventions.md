---
name: FPP File Conventions and Best Practices
description: File naming, organization patterns, .fpp vs .fppi usage, and idiomatic FPP project structure
type: reference
originSessionId: c7708e45-a599-4300-a457-572b467a90ee
---
# FPP File Conventions and Best Practices

## File Extensions

### .fpp Files (Main Source Files)
**Purpose:** Primary FPP source files that are directly analyzed and translated

**Characteristics:**
- Contain complete definitions
- Used as direct input to analysis/translation tools
- Location of definitions (for dependency tracking) is the .fpp file itself

**Common patterns:**
- One component per file: `ComponentName.fpp`
- One port definition per file: `PortName.fpp`  
- Related types grouped: `DataTypes.fpp`
- Module constants: `Constants.fpp`
- Topology definitions: `TopologyName.fpp`

### .fppi Files (Include Files)
**Purpose:** Files meant to be included via `include` specifiers

**Characteristics:**
- Contain fragments/partials of FPP code
- Never directly analyzed or translated
- Location of definitions is the *including* file, NOT the .fppi file
- Used to split large definitions across multiple files

**Common patterns:**
- Component port lists: `ComponentPorts.fppi`
- Component commands: `ComponentCommands.fppi`
- Component events: `ComponentEvents.fppi`
- Component telemetry: `ComponentTelemetry.fppi`
- Component parameters: `ComponentParams.fppi`
- Topology connections: `ConnectionGraphName.fppi`
- Dictionary definitions split: `EventDictionary.fppi`

**Example usage:**
```fpp
# In MyComponent.fpp
active component MyComponent {
  include "MyComponentPorts.fppi"
  include "MyComponentCommands.fppi"
  include "MyComponentEvents.fppi"
}
```

## File Organization Patterns

### By FPP Element Type

**Recommended structure:**
```
module/
├── Types/           # Type definitions
│   ├── Enums.fpp
│   ├── Structs.fpp
│   └── Arrays.fpp
├── Ports/           # Port definitions
│   ├── DataPort.fpp
│   └── CommandPort.fpp
├── Components/      # Component definitions
│   ├── ComponentA.fpp
│   └── ComponentB.fpp
├── Instances/       # Component instances
│   └── Instances.fpp
├── Topologies/      # Topology definitions
│   └── MainTopology.fpp
└── Constants/       # Constants
    └── Limits.fpp
```

### By FSW Role

**Alternative structure:**
```
project/
├── Fw/              # Framework definitions
│   ├── Types/
│   └── Ports/
├── Svc/             # Service components
│   ├── CommandDispatcher/
│   └── RateGroup/
└── App/             # Application components
    ├── Sensors/
    └── Controllers/
```

### Within Component Directory

**For complex components:**
```
ComponentName/
├── ComponentName.fpp           # Main component definition
├── ComponentNamePorts.fppi     # Port instances
├── ComponentNameCommands.fppi  # Command specifiers
├── ComponentNameEvents.fppi    # Event specifiers
├── ComponentNameTlm.fppi       # Telemetry specifiers
├── ComponentNameParams.fppi    # Parameter specifiers
└── ComponentName.cpp           # C++ implementation
```

## Naming Conventions

### Module Names
- PascalCase: `Fw`, `Svc`, `App`, `DataTypes`
- Match C++ namespace convention
- Should match directory structure

### Component Names
- PascalCase: `CommandDispatcher`, `RateGroup`, `TempSensor`
- Descriptive, noun-based
- Component instances typically lowercase: `cmdDispatcher`, `rateGroup`

### Port Names
- PascalCase for definitions: `CmdPort`, `DataPort`
- camelCase for instances: `cmdIn`, `dataOut`
- Suffix with direction: `cmdIn`, `cmdOut`

### Type Names
- PascalCase: `StatusEnum`, `DataStruct`, `Matrix3x3`
- Suffixes optional but can clarify: `Enum`, `Struct`, `Array`

### Constants
- UPPER_SNAKE_CASE or PascalCase depending on context
- Framework uses: `MAX_BUFFER_SIZE`, `DEFAULT_PRIORITY`

### File Names
- Match primary definition: `ComponentName.fpp` for component `ComponentName`
- Include files can be descriptive: `CommonTypes.fppi`, `UtilityPorts.fppi`

## Include Patterns

### Component Definition Split

**Main file:**
```fpp
# MyComponent.fpp
active component MyComponent {
  
  include "MyComponentPorts.fppi"
  
  include "MyComponentCommands.fppi"
  
  include "MyComponentEvents.fppi"
  
  include "MyComponentTlm.fppi"

}
```

**Port file:**
```fpp
# MyComponentPorts.fppi
@ Command input port
command recv port cmdIn

@ Event output port  
event port eventOut
```

### Module Definition Split

**Can split module across files:**
```fpp
# File1.fpp
module M {
  constant a = 0
}

# File2.fpp  
module M {
  constant b = 1  # Merges with module M from File1
}
```

### Topology Connection Split

**Main topology:**
```fpp
# Topology.fpp
topology Main {
  
  include "instances.fppi"
  
  include "CommandConnections.fppi"
  
  include "TelemetryConnections.fppi"

}
```

**Connection file:**
```fpp
# CommandConnections.fppi
connections Commanding {
  dispatcher.cmdOut[0] -> receiver.cmdIn
  receiver.cmdRespOut -> dispatcher.cmdRespIn
}
```

## Location Management

### Locating Definitions

**Use `fpp-locate-defs` to generate location specifiers:**

```bash
# Generate locations for framework types
find Fw -name '*.fpp' | xargs fpp-locate-defs -d Fw > fw-locs.fpp

# Generate locations for service components  
find Svc -name '*.fpp' | xargs fpp-locate-defs -d Svc > svc-locs.fpp
```

**Generated location specifiers:**
```fpp
# fw-locs.fpp
locate type FwSizeType at "Types/FwSizeType.fpp"
locate port Cmd at "Ports/Cmd.fpp"
```

### Location Files Organization

**Recommended:**
```
project/
├── Fw/
│   ├── ... (definitions)
│   └── fpp-locs.fpp        # Auto-generated
├── Svc/  
│   ├── ... (definitions)
│   └── fpp-locs.fpp        # Auto-generated
└── build/
    └── all-locs.fpp        # Combined, auto-generated
```

## Dependency Management Best Practices

### Per-Module Dependencies

**For each module, compute dependencies:**
```bash
# In module directory
fpp-depend \
  ../Fw/fpp-locs.fpp \
  ../Svc/fpp-locs.fpp \
  *.fpp \
  > deps.txt
```

### Check Before Translate

**Always check before generating code:**
```bash
# Check first
fpp-check $(cat deps.txt) MyModule/*.fpp

# If check passes, then translate
fpp-to-cpp -i $(cat deps.txt | tr '\n' ',') MyModule/*.fpp
```

## Module Organization Patterns

### Framework Module Pattern
```
Fw/
├── Types/
│   ├── FwSizeType.fpp
│   └── FwStringType.fpp
├── Ports/
│   ├── Cmd.fpp
│   └── CmdReg.fpp
└── fpp-locs.fpp
```

### Service Module Pattern
```
Svc/
├── CommandDispatcher/
│   ├── CommandDispatcher.fpp
│   └── CommandDispatcherPorts.fppi
├── RateGroup/
│   ├── RateGroup.fpp
│   └── RateGroupPorts.fppi
└── fpp-locs.fpp
```

### Application Module Pattern
```
App/
├── Types/
│   └── AppTypes.fpp
├── Components/
│   ├── SensorManager/
│   └── Controller/
├── Instances.fpp
└── Topology.fpp
```

## Documentation Patterns

### Annotation Usage

**Use pre-annotations for definitions:**
```fpp
@ Manages sensor data collection and processing
@ Provides rate-grouped sensor reading
active component SensorManager {
  
  @ Sensor data input port
  @ Receives raw sensor readings
  async input port sensorIn: SensorData

}
```

**Use post-annotations for parameters:**
```fpp
async command SET_THRESHOLD(
    sensor: U8 @< Sensor ID (0-15)
    threshold: F32 @< Threshold value in sensor units
)
```

### Annotation in Include Files

**Annotations preserved across includes:**
```fpp
# Commands.fppi
@ Initiates sensor calibration sequence
@ Takes approximately 30 seconds
async command CALIBRATE opcode 0x10
```

## Build System Integration

### CMake Pattern (F Prime)

**CMakeLists.txt pattern:**
```cmake
set(SOURCE_FILES
  "${CMAKE_CURRENT_LIST_DIR}/MyComponent.fpp"
)

register_fprime_module()
```

CMake automatically:
- Discovers .fpp files
- Computes dependencies
- Generates C++ code
- Compiles generated and hand-written code

### Manual Build Pattern

**Makefile pattern:**
```makefile
FPP_FILES = $(wildcard *.fpp)
DEPS_FILE = deps.txt
LOC_FILES = ../Fw/fpp-locs.fpp ../Svc/fpp-locs.fpp

$(DEPS_FILE): $(LOC_FILES) $(FPP_FILES)
	fpp-depend $(LOC_FILES) $(FPP_FILES) > $@

cpp: $(DEPS_FILE)
	fpp-to-cpp -i $(shell cat $(DEPS_FILE) | tr '\n' ',') $(FPP_FILES)
```

## Anti-Patterns to Avoid

### Don't Mix .fpp and .fppi Roles
❌ **Bad:** Directly analyzing .fppi files
```bash
fpp-check ComponentPorts.fppi  # Wrong!
```

✅ **Good:** Include .fppi in .fpp, analyze .fpp
```bash
fpp-check Component.fpp  # Correct
```

### Don't Manually Write Location Specifiers
❌ **Bad:** Hand-writing location files
```fpp
# Don't do this manually
locate type MyType at "Types/MyType.fpp"
```

✅ **Good:** Auto-generate with tool
```bash
fpp-locate-defs Types/*.fpp > type-locs.fpp
```

### Don't Use Inconsistent Paths
❌ **Bad:** Mixing relative path styles
```bash
fpp-depend ../Fw/types.fpp  # From one directory
fpp-depend Fw/types.fpp     # From another directory
```

✅ **Good:** Use consistent absolute or managed relative paths

### Don't Ignore Include File Dependencies
When using build systems, ensure .fppi files trigger rebuilds:
```cmake
# CMake tracks .fppi files automatically with F Prime
# For manual builds, track includes:
Component.o: Component.fpp ComponentPorts.fppi
```

## Migration Patterns

### XML to FPP
**Use fpp-from-xml:**
```bash
fpp-from-xml ComponentAi.xml > Component.fpp
```

### Legacy to Modern Structure
1. Convert XML to FPP
2. Split large components using includes  
3. Organize by module
4. Generate location specifiers
5. Update build system
