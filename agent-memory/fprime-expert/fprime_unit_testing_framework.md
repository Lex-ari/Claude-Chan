---
name: F Prime Unit Testing Framework
description: TesterBase, GTestBase, test harnesses, assertion macros, and testing patterns
type: reference
---

# F Prime Unit Testing Framework

F Prime provides comprehensive unit testing support at component level.

## Testing Framework Architecture

### Three-Layer Class Hierarchy

```
TesterBase (autocoded) - Test harness, mirrors component interface
    ↓
GTestBase (autocoded) - GoogleTest support, assertion macros
    ↓
Tester (developer-written) - Test methods, test fixtures
```

### TesterBase (Autocoded)

**Purpose:** Mirror image of component under test

**Provides:**
- **From ports**: For each output port in component, TesterBase has input "from port"
- **To ports**: For each input port in component, TesterBase has output "to port"
- **History buffers**: Stores all data received through from ports
- **Utility methods**: Send commands, invoke ports, set parameters, set time
- **Parameter storage**: Stores parameters for component to retrieve
- **Time storage**: Stores time for component time requests

**Auto-generated from:** Component FPP definition

**Example structure:**
```
Component C has:
    - Input port cmdIn
    - Output port dataOut
    
TesterBase has:
    - Output port (to_cmdIn) → connects to C's cmdIn
    - Input port (from_dataOut) → receives from C's dataOut
    - History of dataOut invocations
```

### GTestBase (Autocoded)

**Purpose:** GoogleTest integration with F Prime-specific assertions

**Provides:**
- Standard GoogleTest macros (`ASSERT_EQ`, `ASSERT_TRUE`, etc.)
- F Prime-specific assertion macros:
  - Command response assertions
  - Event assertions
  - Telemetry assertions
  - Port invocation assertions

**Why separate class:** Optional. Systems without GoogleTest can use TesterBase directly.

### Tester (Developer-Written)

**Purpose:** Contains component under test, implements test methods

**Contains:**
- Component instance (member variable)
- Test fixture setup/teardown
- Test method implementations
- Helper methods for common test operations

**Generated from template:** `fprime-util impl --ut` creates initial template

## Test Harness Operation

### Component Connection to Harness

```
Tester
    ↑ (contains)
Component Under Test
    ↓ output ports connected to ↓
TesterBase from ports (input)
    ↑ to ports (output) connected to ↑  
Component Under Test input ports
```

### Port Invocation Flow

**Testing component output:**
1. Component calls output port
2. TesterBase receives on "from port"
3. Virtual handler stores arguments in history buffer
4. Test can assert on history

**Invoking component input:**
1. Test calls TesterBase "to port" helper
2. Invokes component's input port
3. Component handler executes
4. Test can check results

## Assertion Macros

### Command Response Assertions

```cpp
// Assert total number of command responses
ASSERT_CMD_RESPONSE_SIZE(expectedSize);

// Assert specific command response
ASSERT_CMD_RESPONSE(
    index,                          // Index in history
    expectedOpcode,                 // Expected opcode
    expectedCmdSeq,                 // Expected sequence number
    expectedResponse                // Expected response (OK, ERROR, etc.)
);
```

**Example:**
```cpp
this->sendCmd_SET_MODE(0, 5);  // cmdSeq=0, mode=5
this->component.doDispatch();
ASSERT_CMD_RESPONSE_SIZE(1);
ASSERT_CMD_RESPONSE(0, MyComp::OPCODE_SET_MODE, 0, Fw::CmdResponse::OK);
```

### Event Assertions

```cpp
// Assert total number of all events
ASSERT_EVENTS_SIZE(expectedSize);

// Assert number of specific event
ASSERT_EVENTS_<EventName>_SIZE(expectedSize);

// Assert specific event with arguments
ASSERT_EVENTS_<EventName>(
    index,          // Index in history for this event type
    arg1,           // Expected value of first argument
    arg2,           // Expected value of second argument
    ...
);
```

**Example:**
```cpp
this->sendCmd_SET_MODE(0, 5);
this->component.doDispatch();
ASSERT_EVENTS_SIZE(1);
ASSERT_EVENTS_ModeChanged_SIZE(1);
ASSERT_EVENTS_ModeChanged(0, 5);  // Verify mode argument
```

### Telemetry Assertions

```cpp
// Assert total number of all telemetry updates
ASSERT_TLM_SIZE(expectedSize);

// Assert number of updates on specific channel
ASSERT_TLM_<ChannelName>_SIZE(expectedSize);

// Assert specific telemetry value
ASSERT_TLM_<ChannelName>(
    index,          // Index in history for this channel
    expectedValue   // Expected channel value
);
```

**Example:**
```cpp
this->sendCmd_SET_MODE(0, 5);
this->component.doDispatch();
ASSERT_TLM_SIZE(1);
ASSERT_TLM_CurrentMode_SIZE(1);
ASSERT_TLM_CurrentMode(0, 5);
```

### From Port Assertions

For user-defined output ports:

```cpp
// Assert total invocations on all from ports
ASSERT_FROM_PORT_HISTORY_SIZE(expectedSize);

// Assert number of invocations on specific from port
ASSERT_from_<portName>_SIZE(expectedSize);

// Assert specific port invocation arguments
ASSERT_from_<portName>(
    index,          // Index in history for this port
    arg1,           // Expected value of first argument
    arg2,           // Expected value of second argument
    ...
);
```

**Example:**
```cpp
this->invoke_to_schedIn(0, 0);  // Trigger schedule port
this->component.doDispatch();
ASSERT_FROM_PORT_HISTORY_SIZE(1);
ASSERT_from_dataOut_SIZE(1);
ASSERT_from_dataOut(0, expectedData);
```

## Test Helper Methods

### Sending Commands

```cpp
// Autocoded send command helper
this->sendCmd_<COMMAND_NAME>(
    cmdSeq,         // Command sequence number
    arg1,           // First argument
    arg2,           // Second argument
    ...
);
```

**Always call after sending command:**
```cpp
this->component.doDispatch();  // Dispatches queued messages
```

### Invoking To Ports

```cpp
// Autocoded to port helper
this->invoke_to_<portName>(
    portNum,        // Port number (0 for single port)
    arg1,           // Port argument 1
    arg2,           // Port argument 2
    ...
);
```

### Setting Parameters

```cpp
// Set parameter value in test harness
this->paramSet_<ParamName>(
    value,                  // Parameter value
    Fw::ParamValid::VALID   // Parameter status
);
```

**When component calls getPrm port, receives this value.**

### Setting Time

```cpp
// Set time that component will receive
Fw::Time testTime(1234, 5678);  // seconds, microseconds
this->setTestTime(testTime);
```

**When component calls getTime port, receives this time.**

## Test Structure Best Practices

### Test Method Organization

```cpp
void Tester::testNominalBehavior() {
    // Setup
    this->paramSet_Timeout(100, Fw::ParamValid::VALID);
    
    // Execute
    this->sendCmd_START(0);
    this->component.doDispatch();
    
    // Verify
    ASSERT_CMD_RESPONSE_SIZE(1);
    ASSERT_CMD_RESPONSE(0, MyComp::OPCODE_START, 0, Fw::CmdResponse::OK);
    ASSERT_EVENTS_SIZE(1);
    ASSERT_EVENTS_Started_SIZE(1);
}

void Tester::testErrorHandling() {
    // Setup for error condition
    this->paramSet_Timeout(0, Fw::ParamValid::INVALID);
    
    // Execute
    this->sendCmd_START(0);
    this->component.doDispatch();
    
    // Verify error response
    ASSERT_CMD_RESPONSE_SIZE(1);
    ASSERT_CMD_RESPONSE(0, MyComp::OPCODE_START, 0, Fw::CmdResponse::EXECUTION_ERROR);
    ASSERT_EVENTS_SIZE(1);
    ASSERT_EVENTS_StartFailed_SIZE(1);
}
```

### Common Helper Methods

```cpp
// In Tester class
void Tester::setupNominalState() {
    this->paramSet_Timeout(100, Fw::ParamValid::VALID);
    this->sendCmd_INIT(0);
    this->component.doDispatch();
    this->clearHistory();  // Clear setup history
}

void Tester::clearHistory() {
    this->clearEvents();
    this->clearTlm();
    this->clearFromPortHistory();
}
```

## Testing Guidelines

### Test Against Interface
- Send commands through command interface
- Invoke ports through to ports
- Read component state via public methods
- **Don't** modify component internals directly

### Test Requirements
- Map tests to component requirements
- Document which tests cover which requirements
- Use test names that reflect requirements

### Achieve Code Coverage
- Target 80%+ code coverage
- Use `fprime-util check --coverage` to measure
- Review `.gcov` files to find untested code

### Test Both Paths
- Nominal behavior (success cases)
- Off-nominal behavior (error cases, edge cases)
- Boundary conditions

### Use Helper Methods
- Extract common setup to helper methods
- Avoid code duplication in tests
- Make tests readable and maintainable

## Running Tests

### Build and Run Tests

```bash
# From component directory
fprime-util check                    # Run tests
fprime-util check --all              # Run all tests
fprime-util check --coverage         # Run with coverage
fprime-util check --all --coverage   # All tests with coverage
```

### Coverage Analysis

**Summary files:** `*_gcov.txt` in component directory

**Annotated source:** `*.cpp.gcov`, `*.hpp.gcov` in test/ut directory
- Lines with `#####`: Never executed
- Lines with number: Execution count
- Lines with `-`: Non-executable (comments, declarations)

## Mock vs Real Libraries

### Link Against Real Library
**When:** Component calls library, want to test real integration

**Pros:**
- Tests actual library behavior
- Catches integration issues
- More confidence in component

**Cons:**
- Harder to test error conditions
- May not work on all platforms

### Link Against Mock Library
**When:** Need to inject faults or test error handling

**Pros:**
- Can simulate any library behavior
- Test error cases easily
- Platform-independent

**Cons:**
- Not testing real library
- Must maintain mock

**Configuration:** In component test `CMakeLists.txt`, choose which library to link

## How to apply

1. **Generate templates:** Use `fprime-util impl --ut` to create test skeleton
2. **Write test per requirement:** Each requirement should have corresponding test(s)
3. **Test interface:** Send commands, invoke ports, check outputs - don't access internals
4. **Use assertions:** Leverage F Prime assertion macros for cleaner tests
5. **Clear history:** Between tests or after setup, clear history to avoid false assertions
6. **doDispatch:** Always call after sending async command or port to dispatch queued messages
7. **Coverage goal:** Aim for 80%+ code coverage, review gcov to find gaps
8. **Refactor tests:** Extract common setup to helpers, avoid duplication
9. **Test errors:** Don't just test success - test failure cases and edge cases
10. **Document mapping:** Comment or document which tests cover which requirements
