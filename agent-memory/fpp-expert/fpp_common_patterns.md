---
name: FPP Common Patterns and Idioms
description: Common FPP coding patterns, best practices, idioms for components, ports, topologies, and typical F Prime FSW structures
type: reference
originSessionId: c7708e45-a599-4300-a457-572b467a90ee
---
# FPP Common Patterns and Idioms

## Component Patterns

### Minimal Component Pattern
```fpp
passive component SimpleComponent {
  sync input port run: Svc.Sched
  output port dataOut: DataPort
}
```

**When to use:** Simple components with no commands, events, or telemetry.

### Full-Featured Active Component
```fpp
active component StandardComponent {
  
  # Special ports
  command recv port cmdIn
  command reg port cmdRegOut
  command resp port cmdRespOut
  event port eventOut
  text event port textEventOut
  time get port timeGetOut
  telemetry port tlmOut
  
  # General ports
  async input port schedIn: Svc.Sched
  output port dataOut: [5] DataPort
  
  # Commands
  async command START opcode 0x00
  async command STOP opcode 0x01
  
  # Events
  event STARTED severity activity low format "Component started"
  event STOPPED severity activity low format "Component stopped"
  
  # Telemetry
  telemetry State: U8 update on change
  telemetry Counter: U32
}
```

**When to use:** Standard active component with F Prime integration.

### Component with Parameters
```fpp
active component ConfigurableComponent {
  
  # Special ports (including parameter ports)
  command recv port cmdIn
  command reg port cmdRegOut
  command resp port cmdRespOut
  param get port prmGetOut
  param set port prmSetOut
  
  # Parameters with defaults
  param SAMPLE_RATE: F32 default 10.0
  param ENABLE_LOGGING: bool default false
  param MAX_RETRIES: U32 default 3
}
```

**When to use:** Components with configurable behavior.

### Driver Component Pattern
```fpp
active component DeviceDriver {
  
  # Special ports
  command recv port cmdIn
  command reg port cmdRegOut
  command resp port cmdRespOut
  event port eventOut
  text event port textEventOut
  time get port timeGetOut
  
  # Schedule input (periodic polling)
  async input port schedIn: Svc.Sched
  
  # Hardware interface
  output port deviceOut: HardwarePort
  async input port deviceIn: HardwarePort
  
  # Data output to application
  output port dataOut: DataPort
  
  # Commands
  async command ENABLE_DEVICE opcode 0x00
  async command DISABLE_DEVICE opcode 0x01
  async command READ_DEVICE(reg: U32) opcode 0x02
  
  # Events
  event DEVICE_ENABLED severity activity low
  event DEVICE_ERROR(code: U32) severity warning high
  
  # Telemetry
  telemetry DeviceStatus: U8
}
```

**When to use:** Hardware device drivers.

### Data Processing Component Pattern
```fpp
queued component DataProcessor {
  
  # Input from multiple sources
  async input port dataIn: [10] DataPort
  
  # Output to consumers
  output port processedOut: ProcessedDataPort
  
  # Configuration
  sync input port configure: ConfigPort
  
  # Special ports
  event port eventOut
  telemetry port tlmOut
  time get port timeGetOut
  
  # Events
  event DATA_PROCESSED(count: U32) severity diagnostic
  event PROCESSING_ERROR severity warning high
  
  # Telemetry
  telemetry InputCount: U32
  telemetry OutputCount: U32
  telemetry ErrorCount: U32
}
```

**When to use:** Components that process data from multiple sources.

## Port Patterns

### Request-Response Pattern
```fpp
# Request port
port RequestPort(
    reqId: U32 @< Request identifier
    data: RequestData @< Request data
)

# Response port  
port ResponsePort(
    reqId: U32 @< Request identifier
    status: U8 @< Response status
    data: ResponseData @< Response data
)

# Component using pattern
active component Requester {
  output port request: RequestPort
  async input port response: ResponsePort
}

active component Responder {
  async input port request: RequestPort
  output port response: ResponsePort
}

# Topology connection
topology T {
  instance req: Requester base id 0x100
  instance resp: Responder base id 0x200
  
  connections C {
    req.request -> resp.request
    resp.response -> req.response
  }
}
```

**When to use:** Asynchronous request-response communication.

### Data Flow Pattern
```fpp
# Data port
port DataPort(
    timestamp: U64
    ref data: DataBuffer
)

# Producer
passive component Producer {
  sync input port trigger: Svc.Sched
  output port dataOut: DataPort
}

# Processor
queued component Processor {
  async input port dataIn: DataPort
  output port dataOut: DataPort
}

# Consumer
passive component Consumer {
  async input port dataIn: DataPort
}
```

**When to use:** Data pipeline processing.

### Buffered Port Pattern
```fpp
port BufferedPort(
    ref buffer: Fw.Buffer @< Pass buffer by reference
)

active component BufferManager {
  # Provides buffers
  sync input port bufferGet: Fw.BufferGet
  
  # Receives buffers back
  async input port bufferReturn: Fw.BufferSend
}
```

**When to use:** Zero-copy data transfer with large buffers.

## Topology Patterns

### Layered Topology Pattern
```fpp
# Service layer
topology ServiceTopology {
  instance cmdDisp: Svc.CommandDispatcher base id 0x0100
  instance eventLogger: Svc.EventLogger base id 0x0200
  instance tlmDb: Svc.TelemetryDb base id 0x0300
  
  connections Dispatch {
    command
    event
    telemetry
  }
  
  # Expose ports for application layer
  port cmdInExt = cmdDisp.seqCmdBuff
  port tlmOut = tlmDb.tlmOut
}

# Application topology
topology AppTopology {
  # Import service topology
  instance services: ServiceTopology
  
  # Application components
  instance sensor: App.Sensor base id 0x1000
  instance controller: App.Controller base id 0x2000
  
  connections AppConnections {
    sensor.dataOut -> controller.dataIn
  }
  
  connections ServiceConnections {
    # Connect to service layer
    sensor.cmdIn -> services.cmdInExt
  }
}
```

**When to use:** Separate framework services from application components.

### Rate Group Pattern
```fpp
topology RateGroupTopology {
  instance rateGroup1Hz: Svc.RateGroup base id 0x1000
  instance rateGroup10Hz: Svc.RateGroup base id 0x2000
  
  instance comp1: Component1 base id 0x3000
  instance comp2: Component2 base id 0x4000
  
  connections RateGroups {
    # 1Hz components
    rateGroup1Hz.RateGroupMemberOut[0] -> comp1.schedIn
    
    # 10Hz components
    rateGroup10Hz.RateGroupMemberOut[0] -> comp2.schedIn
  }
}
```

**When to use:** Periodic component execution at different rates.

### Health Monitoring Pattern
```fpp
topology HealthTopology {
  instance healthMon: Svc.Health base id 0x1000
  instance comp1: Component1 base id 0x2000
  instance comp2: Component2 base id 0x3000
  
  connections HealthConnections {
    # Health pings
    healthMon.PingSend[0] -> comp1.pingIn
    healthMon.PingSend[1] -> comp2.pingIn
    
    # Health responses
    comp1.pingOut -> healthMon.PingReturn[0]
    comp2.pingOut -> healthMon.PingReturn[1]
  }
}
```

**When to use:** Component health monitoring and fault detection.

## Type Patterns

### Status Enum Pattern
```fpp
enum Status: U8 {
  OK = 0
  ERROR = 1
  BUSY = 2
  TIMEOUT = 3
} default OK
```

**When to use:** Return status values in ports and events.

### Configuration Struct Pattern
```fpp
struct Config {
  enabled: bool
  sampleRate: F32 format "{.1f}"
  maxSamples: U32
  threshold: [3] F32
} default {
  enabled = true
  sampleRate = 10.0
  maxSamples = 1000
}
```

**When to use:** Grouping related configuration values.

### Telemetry Data Struct Pattern
```fpp
struct TelemetryData {
  timestamp: U64
  temperature: F32 format "{.2f}"
  pressure: F32 format "{.3f}"
  altitude: F32 format "{.1f}"
}
```

**When to use:** Bundling related telemetry in single structure.

### Fixed-Size Buffer Pattern
```fpp
array Buffer256 = [256] U8
array Buffer1K = [1024] U8
array Buffer4K = [4096] U8
```

**When to use:** Fixed-size buffers for communication.

## Module Organization Patterns

### Framework Types Module
```fpp
module Fw {
  
  @ Framework size type
  type FwSizeType = U32
  
  @ Framework index type
  type FwIndexType = U32
  
  @ Opcode type
  type FwOpcodeType = U32
  
  @ Port numbers
  array PortNumbers = [10] U32
}
```

**When to use:** Framework-level type definitions.

### Application Types Module
```fpp
module App {
  
  module Types {
    
    @ Sensor data types
    enum SensorType { TEMP, PRESSURE, HUMIDITY }
    
    struct SensorReading {
      sensorType: SensorType
      value: F32
      timestamp: U64
    }
    
    @ Control modes
    enum ControlMode { MANUAL, AUTO, SAFE }
  }
  
  module Ports {
    @ Sensor data port
    port SensorData(reading: Types.SensorReading)
  }
}
```

**When to use:** Application-specific types and ports.

## State Machine Patterns

### Simple Two-State Machine
```fpp
state machine Device {
  
  signal Enable
  signal Disable
  
  initial enter OFF
  
  state OFF {
    on Enable enter ON
  }
  
  state ON {
    on Disable enter OFF
  }
}
```

**When to use:** On/off or enabled/disabled behavior.

### Multi-State with Error Handling
```fpp
state machine Controller {
  
  signal Start
  signal Stop
  signal Error
  signal Reset
  
  initial enter IDLE
  
  state IDLE {
    on Start enter STARTING
  }
  
  state STARTING {
    on Success enter RUNNING
    on Error enter ERROR
  }
  
  state RUNNING {
    on Stop enter STOPPING
    on Error enter ERROR
  }
  
  state STOPPING {
    on Success enter IDLE
    on Error enter ERROR
  }
  
  state ERROR {
    on Reset enter IDLE
  }
}
```

**When to use:** Complex lifecycle with error recovery.

## Command Patterns

### Immediate Command Pattern
```fpp
@ Set LED state immediately
sync command SET_LED(
    state: bool @< LED state (true=on, false=off)
) opcode 0x10
```

**When to use:** Fast operations that complete immediately.

### Queued Command Pattern
```fpp
@ Initiate calibration sequence
async command START_CALIBRATION(
    duration: U32 @< Calibration duration in seconds
) opcode 0x20 priority 10
```

**When to use:** Long-running operations.

### Command Sequence Pattern
```fpp
async command STEP1 opcode 0x30
async command STEP2 opcode 0x31
async command STEP3 opcode 0x32

event STEP1_COMPLETE severity activity low
event STEP2_COMPLETE severity activity low
event STEP3_COMPLETE severity activity low
```

**When to use:** Multi-step operations triggered by ground.

## Event Patterns

### Progress Reporting Pattern
```fpp
event OPERATION_STARTED severity activity low \
  format "Operation started"

event OPERATION_PROGRESS(percent: U8) severity activity low \
  format "Operation {}% complete"

event OPERATION_COMPLETE severity activity low \
  format "Operation complete"
```

**When to use:** Long operations requiring progress updates.

### Error Context Pattern
```fpp
event ERROR_OCCURRED(
    errorCode: U32 @< Error code
    context: string size 80 @< Error context
    file: string size 40 @< Source file
    line: U32 @< Source line
) severity warning high \
  format "Error {}: {} ({}:{})"
```

**When to use:** Detailed error reporting with context.

### Throttled Diagnostic Pattern
```fpp
event DEBUG_VALUE(
    id: U8
    value: F32
) severity diagnostic \
  format "Debug {}: {.4f}" \
  throttle 100 every { seconds = 10 }
```

**When to use:** High-frequency diagnostic events.

## Include File Organization Pattern

### Component with Includes
```fpp
# Component.fpp
active component MyComponent {
  
  # Constants
  include "ComponentConstants.fppi"
  
  # Types
  include "ComponentTypes.fppi"
  
  # Ports
  include "ComponentPorts.fppi"
  
  # Commands
  include "ComponentCommands.fppi"
  
  # Events  
  include "ComponentEvents.fppi"
  
  # Telemetry
  include "ComponentTelemetry.fppi"
  
  # Parameters
  include "ComponentParams.fppi"
}
```

**When to use:** Large components with many definitions.

## Error Handling Patterns

### Return Status Pattern
```fpp
enum OpStatus: U8 {
  SUCCESS = 0
  ERROR_INVALID_PARAM = 1
  ERROR_TIMEOUT = 2
  ERROR_RESOURCE = 3
}

port OperationPort(
    param: U32
) -> OpStatus

# Handler returns status
```

**When to use:** Synchronous operations needing status return.

### Error Event Pattern
```fpp
# Define error enum
enum ErrorCode: U32 {
  NO_ERROR = 0
  TIMEOUT = 1
  INVALID_DATA = 2
}

# Events for errors
event ERROR(
    code: ErrorCode
    context: U32
) severity warning high format "Error {}: {}"

# Telemetry tracks last error
telemetry LastError: ErrorCode
```

**When to use:** Tracking and reporting errors.
