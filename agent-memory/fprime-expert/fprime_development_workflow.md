---
name: F Prime Development Workflow
description: Standard F Prime development process from requirements to integration testing
type: reference
---

# F Prime Development Workflow

Standard process used by F Prime developers, supported by F Prime tooling.

## 1. High-Level Design

**Activities:**
- Specify system-level requirements
- Create block diagram of key system functionality
- Break functionality into discrete units (future components)
- Define interfaces between units (future ports)
- Design full system topology (components + port connections)

**Outputs:**
- System requirements document
- Block diagram / architecture diagram
- Component list with responsibilities
- Port interface definitions
- Topology diagram

**Review F Prime framework components:**
Check which components can be inherited from framework (CmdDispatcher, EventLogger, TlmChan, etc.) vs. which must be custom-implemented.

## 2. Setup Deployment

Prepare development environment and deployment structure.

### Option A: In-Tree Deployment
- Create deployment within F Prime git repository
- Copy `Ref` application as starting point
- Simpler setup, but mixes mission code with framework
- Harder to update F Prime later

### Option B: Standalone Deployment (Recommended)
- Create deployment outside F Prime repository
- F Prime as git submodule or external reference
- Separates mission code from framework
- Easier to update F Prime independently

**Repository structure (standalone):**
```
mission/
├── mission_deployment/
│   ├── Components/
│   ├── Top/
│   ├── CMakeLists.txt
│   └── settings.ini
├── fprime/ (git submodule)
└── external_lib/ (git submodule)
```

**Configure `settings.ini`:**
- Set deployment toolchain
- Specify library locations
- Point to F Prime framework location (standalone only)
- Configure build options

**Starting point:** Copy and modify `Ref` application from F Prime

## 3. Develop Components

Assign developers to components. Each component goes through:

### 3a. Design and Requirements

Using high-level requirements, define:
- Component-specific requirements
- Component behaviors
- Interfaces with other components (ports)
- Commands, events, telemetry, parameters

### 3b. Create Ports

**Manual approach:**
1. Create port directory (if new)
2. Create port `.fpp` file defining port type
3. Add to `SOURCE_FILES` in `CMakeLists.txt`
4. Add directory to deployment cmake with `add_fprime_subdirectory`

**Automated approach:**
```bash
fprime-util new --port
```
Prompts for port information, generates files, updates CMakeLists automatically.

**Port definition example:**
```fpp
@ Get temperature reading
port GetTemperature() -> F32
```

### 3c. Create Component Definition

**Manual approach:**
1. Create component directory
2. Create `.fpp` file with component definition
3. Optional: Create separate `.fppi` files for commands/events/telemetry
4. Create `CMakeLists.txt`, add component to `SOURCE_FILES`
5. Add directory to deployment cmake with `add_fprime_subdirectory`

**Automated approach (recommended):**
```bash
fprime-util new --component
```

Prompts walk through:
- Component name and type (passive/active/queued)
- Ports to include
- Commands, events, telemetry, parameters
- Auto-generates .fpp, CMakeLists.txt, SDD template
- Option to generate implementation stubs
- Option to generate unit test skeleton

**Component FPP example:**
```fpp
module MyProject {
    @ Temperature sensor component
    passive component TempSensor {
        
        # Ports
        output port dataOut: SensorData
        sync input port schedIn: Svc.Sched
        
        # Commands
        @ Enable sensor
        async command ENABLE()
        
        # Events
        event SensorEnabled() \
            severity activity high \
            format "Sensor enabled"
        
        # Telemetry
        telemetry CurrentTemp: F32
        
        # Parameters
        param SampleRate: U32 default 10
    }
}
```

### 3d. Component Implementation

**Generate implementation templates:**
```bash
fprime-util impl
```

Generates `-template.cpp` and `-template.hpp` files with:
- Constructor stubs
- Pure virtual function stubs (handlers)
- Member variable sections

**Or:** Already generated if using `fprime-util new --component` with implementation option.

**Implementation tasks:**
1. Rename `-template` files (remove `-template` suffix)
2. Fill in constructor initialization
3. Implement all port handlers (pure virtual functions)
4. Implement all command handlers
5. Call telemetry writes, event logs as needed
6. Access parameters via `paramGet_<name>()`

**Build to check errors:**
```bash
fprime-util build
```

### 3e. Component Unit Testing

**Create test skeleton (manual):**
1. Create `test/` directory in component
2. Run `fprime-util impl --ut` to generate test templates
3. Add `UT_SOURCE_FILES` and `register_fprime_ut()` to component `CMakeLists.txt`

**Or:** Already generated if using `fprime-util new --component` with test option.

**Test framework classes:**
- **TesterBase**: Autocoded test harness, mirrors component interface
- **GTestBase**: Adds GoogleTest assertions for events/telemetry/commands
- **Tester**: Developer-written test class, contains component under test

**Write tests:**
```cpp
void Tester::testNominalCommand() {
    // Send command
    this->sendCmd_SET_MODE(0, 1, 5);  // cmdSeq, arg1
    this->component.doDispatch();
    
    // Check command response
    ASSERT_CMD_RESPONSE_SIZE(1);
    ASSERT_CMD_RESPONSE(0, 
        MyComponent::OPCODE_SET_MODE,
        0,
        Fw::CmdResponse::OK);
    
    // Check event
    ASSERT_EVENTS_SIZE(1);
    ASSERT_EVENTS_ModeChanged(0, 1, 5);
    
    // Check telemetry
    ASSERT_TLM_SIZE(1);
    ASSERT_TLM_CurrentMode(0, 5);
}
```

**Run tests:**
```bash
fprime-util check              # Run tests
fprime-util check --coverage   # Run with coverage
fprime-util check --all        # Run all tests
```

**Review coverage:**
- Summary: `*.gcov.txt` files in component directory
- Annotated source: `*.cpp.gcov`, `*.hpp.gcov` files

**Best practices:**
- Test against interface (send commands, check outputs)
- Don't modify component state directly in tests
- Aim for ~80%+ code coverage
- Test requirements, not just code paths

## 4. Assemble Topology

As components complete, add them to topology.

**Topology FPP (`Top/topology.fpp`):**
```fpp
module MyProject {
    topology MyTopology {
        
        # Component instances
        instance cmdDisp: Svc.CmdDispatcher base id 0x100
        instance myComp: MyComponent base id 0x200
        
        # Connections
        connections Commanding {
            cmdDisp.compCmdSend[0] -> myComp.CmdDisp
            myComp.CmdStatus -> cmdDisp.compCmdStat[0]
            myComp.CmdReg -> cmdDisp.compCmdReg[0]
        }
        
        connections Telemetry {
            myComp.Tlm -> tlmChan.TlmRecv
            myComp.Time -> timeSource.timeGetPort
        }
    }
}
```

**Topology C++ (`Top/Topology.cpp`):**
Fill in generated functions:
- `configureTopology()`: Create instances, call init, connect ports
- `setupTopology()`: Register commands, load parameters
- `startTopology()`: Start active component threads
- `teardownTopology()`: Stop threads, cleanup

**Build deployment:**
```bash
fprime-util build
```

## 5. Integration Testing

Test system-level behaviors with F Prime GDS (Ground Data System).

**GDS provides:**
- Command sending
- Event viewing
- Telemetry monitoring
- Sequence execution

**Integration test approach:**
Use GDS Python API to write automated tests:

```python
from fprime_gds.common.testing_fw import GdsTestAPI

class TestMySystem(GdsTestAPI):
    def test_nominal_sequence(self):
        # Send command
        self.send_command("myComp.SET_MODE", [5])
        
        # Check for event
        event = self.get_event_pred("ModeChanged", [5])
        self.assert_event_count(1, event)
        
        # Check telemetry
        channel = self.get_telemetry_pred("CurrentMode")
        self.assert_telemetry_value(5, channel)
```

**Run GDS:**
```bash
fprime-gds
```

**Integration test guide:** See GDS test API documentation

## Complete Development Cycle Summary

```
Requirements → Design
    ↓
Setup Deployment (settings.ini, CMakeLists)
    ↓
For each component:
    Port Design → Component FPP → Implementation → Unit Tests
    ↓
Add to Topology (FPP + C++)
    ↓
Build & Test Deployment
    ↓
Integration Testing (GDS)
```

## Best Practices

1. **Start small:** Build topology incrementally, test subsystems as you go
2. **Test early:** Unit test as you implement, integration test as components integrate
3. **Use fprime-util tools:** Automate component/port generation, building, testing
4. **Follow conventions:** Use standard F Prime patterns for commands/events/telemetry
5. **Document as you go:** Update SDD documents during development
6. **Version control:** Commit frequently, use branches for features
7. **Review topology:** Validate port connections with FPP checks
8. **Size queues appropriately:** Base on expected message rates
9. **Consider threading:** Understand execution contexts, avoid blocking
10. **Leverage framework:** Use existing Svc components where possible

## Common Tools

| Tool | Purpose |
|------|---------|
| `fprime-util new --component` | Generate component skeleton |
| `fprime-util new --port` | Generate port skeleton |
| `fprime-util impl` | Generate implementation templates |
| `fprime-util impl --ut` | Generate unit test templates |
| `fprime-util build` | Build component or deployment |
| `fprime-util check` | Run unit tests |
| `fprime-util check --coverage` | Run unit tests with coverage |
| `fprime-gds` | Launch Ground Data System |

## How to apply

This is the proven workflow. Deviations are fine, but this provides structure:
1. Design before coding
2. Port definitions separate from components
3. Component FPP before implementation
4. Unit tests alongside implementation
5. Incremental topology assembly
6. Integration testing continuously
