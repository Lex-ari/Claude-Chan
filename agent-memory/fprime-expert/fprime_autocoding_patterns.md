---
name: F Prime Autocoding Patterns
description: Autocoded function naming, handler signatures, helper functions, and code generation patterns
type: reference
---

# F Prime Autocoding Patterns

Understanding autocoded functions is critical for implementing F Prime components correctly.

## Autocoded Function Naming Conventions

### Input Port Handlers (IMPLEMENT THESE)

**Signature:**
```cpp
void <portName>_handler(
    NATIVE_INT_TYPE portNum,
    <port arguments>
) = 0;  // Pure virtual
```

**Example:**
```cpp
void schedIn_handler(NATIVE_INT_TYPE portNum, U32 context);
void dataIn_handler(NATIVE_INT_TYPE portNum, const Fw::Buffer& buff);
```

**Where:** Protected section of generated base class
**Your job:** Implement in derived class
**When called:** When another component invokes this input port

### Output Port Invocation (CALL THESE)

**Signature:**
```cpp
void <portName>_out(
    NATIVE_INT_TYPE portNum,
    <port arguments>
);
```

**Example:**
```cpp
this->dataOut_out(0, buffer);
this->statusOut_out(0, Fw::Success);
```

**Where:** Protected section of generated base class
**Your job:** Call from derived class to invoke connected component
**What happens:** Invokes handler on connected input port

### Command Handlers (IMPLEMENT THESE)

**Signature:**
```cpp
void <mnemonic>_cmdHandler(
    FwOpcodeType opCode,
    U32 cmdSeq,
    <command arguments>
) = 0;  // Pure virtual
```

**Example:**
```cpp
void SET_MODE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, U32 mode);
```

**Your job:** 
1. Implement command logic
2. **MUST** call `cmdResponse_out()` when complete:
```cpp
this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
```

**Possible responses:**
- `Fw::CmdResponse::OK`: Success
- `Fw::CmdResponse::ERROR`: Failure
- `Fw::CmdResponse::FATAL`: Fatal error
- `Fw::CmdResponse::EXECUTION_ERROR`: Execution error
- `Fw::CmdResponse::VALIDATION_ERROR`: Argument validation error

### Telemetry Channel Writing (CALL THESE)

**Signature:**
```cpp
void tlmWrite_<channelName>(
    <type>& arg,
    Fw::Time _tlmTime = Fw::Time()
);
```

**Example:**
```cpp
this->tlmWrite_Temperature(currentTemp);
this->tlmWrite_Status(statusEnum);
```

**Where:** Protected section of generated base class
**Your job:** Call whenever channel value should be updated
**What happens:** Updates value in TlmChan, gets time tag internally if not provided

### Event Logging (CALL THESE)

**Signature:**
```cpp
void log_<severity>_<eventName>(
    <event arguments>
);
```

**Example:**
```cpp
this->log_ACTIVITY_HI_ModeChanged(oldMode, newMode);
this->log_WARNING_HI_TemperatureOutOfRange(currentTemp, maxTemp);
this->log_FATAL_CriticalFailure(errorCode);
```

**Severities:** DIAGNOSTIC, ACTIVITY_LO, ACTIVITY_HI, WARNING_LO, WARNING_HI, FATAL, COMMAND

**What happens:** Adds time tag, sends to Log and TextLog output ports

### Parameter Access (CALL THESE)

**Signature:**
```cpp
<parameterType> paramGet_<parameterName>(
    Fw::ParamValid& valid
);
```

**Example:**
```cpp
Fw::ParamValid valid;
U32 timeout = this->paramGet_Timeout(valid);
if (valid == Fw::ParamValid::VALID) {
    // Use timeout value
} else {
    // Handle invalid/default/uninitialized parameter
}
```

**When to check valid:**
- `PARAM_VALID`: Successfully retrieved
- `PARAM_INVALID`: Failed, no default
- `PARAM_DEFAULT`: Failed, using default
- `PARAM_UNINIT`: loadParameters() never called

### Parameter Update Notification (OPTIONALLY IMPLEMENT)

**Signature:**
```cpp
void parameterUpdated(FwPrmIdType id);  // Virtual, default empty
```

**Your job:** Override if need notification when parameter updated by command
**When called:** After parameter value changed by set command

## Port Number Helpers (CALL THESE)

**Get port count:**
```cpp
NATIVE_INT_TYPE getNum_<portName>_InputPorts();
NATIVE_INT_TYPE getNum_<portName>_OutputPorts();
```

**Check connection status:**
```cpp
bool isConnected_<portName>_OutputPort(NATIVE_INT_TYPE portNum);
```

**Example:**
```cpp
for (NATIVE_INT_TYPE i = 0; i < this->getNum_cmdOut_OutputPorts(); i++) {
    if (this->isConnected_cmdOut_OutputPort(i)) {
        this->cmdOut_out(i, cmdId, args);
    }
}
```

## Command Registration (CALL THIS DURING INIT)

**Signature:**
```cpp
void regCommands();
```

**When:** Called during topology setup, after command ports connected
**What happens:** Registers all component commands with dispatcher via CmdReg port

## Parameter Loading (CALL THIS DURING INIT)

**Signature:**
```cpp
void loadParameters();
```

**When:** Called during topology setup, after parameter ports connected
**What happens:** Retrieves all component parameters from PrmDb, caches locally

## Internal Interfaces (ADVANCED)

For components with internal interfaces defined in FPP:

**Invoke function (CALL THIS):**
```cpp
void <interfaceName>_internalInterfaceInvoke(<arguments>);
```

**Handler (IMPLEMENT THIS):**
```cpp
void <interfaceName>_internalInterfaceHandler(<arguments>) = 0;
```

**Use case:** Send message to own component queue for later processing

## Message Pre-Hooks (OPTIONAL)

For async ports and commands, can implement lightweight pre-message-dispatch hook:

**Port pre-hook (OVERRIDE IF NEEDED):**
```cpp
void <portName>_preMsgHook(
    NATIVE_INT_TYPE portNum,
    <port arguments>
);  // Virtual, default empty
```

**Command pre-hook (OVERRIDE IF NEEDED):**
```cpp
void <commandMnemonic>_preMsgHook(
    FwOpcodeType opCode,
    U32 cmdSeq
);  // Virtual, default empty
```

**When called:** Before message placed on queue
**Execution context:** Caller's thread (not component thread)
**Use case:** Quick preprocessing before queueing (be fast!)

## Active Component Thread Lifecycle (OPTIONAL)

**Preamble (OVERRIDE IF NEEDED):**
```cpp
void preamble();  // Virtual, default empty
```

**When called:** Once on component thread before message loop starts

**Finalizer (OVERRIDE IF NEEDED):**
```cpp
void finalizer();  // Virtual, default empty
```

**When called:** Once on component thread after message loop exits

**Use case:** Thread-specific initialization/cleanup

## Time Access (CALL THIS)

**Get current time:**
```cpp
Fw::Time getTime();
```

**What happens:** Calls Time output port to get current time from time source
**When to use:** Need timestamp for custom purposes (events/telemetry get automatic time tags)

## Component Initialization Constructors

**With object names (FW_OBJECT_NAMES enabled):**
```cpp
MyComponent(const char* name);
```

**Without object names (FW_OBJECT_NAMES disabled):**
```cpp
MyComponent();
```

**Implementation pattern:**
```cpp
#if FW_OBJECT_NAMES
MyComponent::MyComponent(const char* name) :
    MyComponentComponentBase(name),
    m_myMemberVar(0)
{
}
#else
MyComponent::MyComponent() :
    MyComponentComponentBase(),
    m_myMemberVar(0)
{
}
#endif
```

## State Machine Autocoding (Advanced)

For components with state machine instances:

**Get state:**
```cpp
<StateMachine>::State <smName>_getState() const;
```

**Send signal:**
```cpp
void <smName>_sendSignal_<signalName>(<signal data if any>);
```

**Action handler (IMPLEMENT):**
```cpp
void <StateMachine>_action_<actionName>(
    SmId smId,
    <StateMachine>::Signal signal,
    <action data if any>
);
```

**Guard handler (IMPLEMENT):**
```cpp
bool <StateMachine>_guard_<guardName>(
    SmId smId,
    <StateMachine>::Signal signal,
    <guard data if any>
) const;
```

## How to apply

1. **Learn the patterns:** Naming is consistent. `<name>_handler` = implement, `<name>_out` = call
2. **Pure virtual = must implement:** If compilation fails with "pure virtual function", you forgot a handler
3. **Protected section:** All autocoded functions in protected section of base class - accessible in derived class
4. **Command response mandatory:** Every command handler MUST call `cmdResponse_out()` exactly once
5. **Port arrays:** `portNum` distinguishes which port in array. Always 0 for single ports.
6. **Check connection:** Optional output ports should check `isConnected` before calling
7. **Pre-hooks are synchronous:** Run on caller thread, be very fast
8. **Lifecycle hooks run on component thread:** preamble/finalizer safe to access component state
9. **Look at generated code:** Build directory has generated base classes - read them to understand available functions
10. **FW_OBJECT_NAMES:** Always support both constructor forms with `#if FW_OBJECT_NAMES`
