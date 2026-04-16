---
name: F' Component State Management
description: Component state variables, thread safety, and guard patterns
type: feedback
---

# F' Component State Management

Proper state management is critical for correct and safe component behavior, especially in multi-threaded active components.

## Component State Variables

### Member Variable Placement

Component state is stored in **private member variables** in the component class:

```cpp
class MyComponent : public MyComponentBase {
private:
    // State variables
    U32 m_counter;
    F64 m_filteredValue;
    MyEnum m_currentMode;
    bool m_initialized;
};
```

**Naming convention:** Use `m_` prefix for member variables (framework convention).

## Thread Safety Considerations

### Passive Components
**Thread model:** No dedicated thread; handlers execute on caller's thread

**State access:** Potentially called from multiple threads
- Must protect state with mutexes if multiple callers
- Or ensure only single-threaded access by design
- Or use only stateless operations

**Example:**
```cpp
class PassiveCounter : public PassiveCounterBase {
private:
    Os::Mutex m_mutex;  // Protect state
    U32 m_counter;

public:
    void increment_handler() {
        this->m_mutex.lock();
        this->m_counter++;
        this->m_mutex.unlock();
    }

    U32 getCount_handler() {
        this->m_mutex.lock();
        U32 count = this->m_counter;
        this->m_mutex.unlock();
        return count;
    }
};
```

### Active Components
**Thread model:** Dedicated thread dispatches messages from queue

**State access in async handlers:** Inherently thread-safe
- Async handlers execute on component's thread only
- Messages dispatched sequentially from queue
- No concurrent access to state within async handlers
- **No mutexes needed for member variables**

**State access in sync handlers:** NOT thread-safe
- Sync handlers execute on caller's thread
- May run concurrently with component's thread
- **Must protect state with mutexes** or use guarded ports

**Example:**
```cpp
class ActiveCounter : public ActiveCounterBase {
private:
    U32 m_counter;  // No mutex needed for async handlers

public:
    // Async handler - runs on component thread, no mutex needed
    void increment_handler(NATIVE_INT_TYPE portNum) {
        this->m_counter++;  // Safe - only this thread accesses
        this->tlmWrite_Counter(this->m_counter);
    }

    // Sync handler - runs on caller's thread, NEEDS protection
    U32 getCount_handler(NATIVE_INT_TYPE portNum) {
        // NOT SAFE - concurrent access with increment_handler!
        return this->m_counter;  // Race condition!
    }
};
```

## Guard Patterns for Thread Safety

### Pattern 1: Guarded Input Ports

**Best solution for sync ports on active components:**

In FPP:
```fpp
guarded input port getCount: DataGet
```

Generated code adds mutex protection:
```cpp
// Framework-generated code (simplified)
ReturnType getCount_handler(NATIVE_INT_TYPE portNum, Args...) {
    this->m_guardMutex.lock();
    ReturnType result = this->getCount_handler_base(portNum, args...);
    this->m_guardMutex.unlock();
    return result;
}
```

**Why guarded ports:** Framework handles locking automatically, prevents deadlock, ensures consistency.

### Pattern 2: Manual Mutex Protection

For complex access patterns or multiple related fields:

```cpp
class MyComponent : public MyComponentBase {
private:
    Os::Mutex m_stateMutex;
    U32 m_counter;
    F64 m_average;
    bool m_valid;

public:
    // Sync handler with manual locking
    void getState_handler(U32& counter, F64& average, bool& valid) {
        this->m_stateMutex.lock();
        counter = this->m_counter;
        average = this->m_average;
        valid = this->m_valid;
        this->m_stateMutex.unlock();
    }

    // Async handler with manual locking
    void updateState_handler(U32 newCounter, F64 newAverage) {
        this->m_stateMutex.lock();
        this->m_counter = newCounter;
        this->m_average = newAverage;
        this->m_valid = true;
        this->m_stateMutex.unlock();
    }
};
```

**When to use:**
- Multiple related fields that must be read/written atomically
- Complex state transitions requiring multiple operations
- Guarded ports insufficient

### Pattern 3: Lockless for Async-Only Access

If ALL state access is through async handlers:

```cpp
class AsyncOnlyComponent : public AsyncOnlyComponentBase {
private:
    // No mutex needed - only async handlers access state
    U32 m_counter;
    F64 m_value;

public:
    // All handlers are async
    void increment_handler(NATIVE_INT_TYPE portNum) {
        this->m_counter++;  // Safe - only component thread
    }

    void setValue_handler(NATIVE_INT_TYPE portNum, F64 value) {
        this->m_value = value;  // Safe - only component thread
    }
};
```

**Advantage:** No mutex overhead, simpler code, no deadlock risk.

**Requirement:** Absolutely NO sync input ports that access state.

## State Initialization

### Constructor Initialization

```cpp
MyComponent::MyComponent(const char* name) :
    MyComponentBase(name),
    m_counter(0),           // Initialize state
    m_value(0.0),
    m_mode(MODE_IDLE),
    m_initialized(false)
{
}
```

### preamble() Method

For active components, use `preamble()` for initialization requiring:
- Time port (for timestamps)
- Parameter loading
- Other port calls

```cpp
void MyComponent::preamble() {
    // Called once before message loop starts
    this->loadParameters();  // Load parameters from PrmDb

    // Initialize state based on parameters
    this->m_threshold = this->paramGet_THRESHOLD();

    // Emit initialization event
    this->log_ACTIVITY_HI_Initialized();
}
```

**Why preamble?** Constructor runs before ports are connected and topology is initialized. Preamble runs after full initialization but before message processing starts.

## State Transition Patterns

### Pattern 1: Mode/State Enum

```cpp
enum OperationalMode {
    MODE_IDLE,
    MODE_ACTIVE,
    MODE_SAFE,
    MODE_ERROR
};

class MyComponent : public MyComponentBase {
private:
    OperationalMode m_mode;

public:
    void setMode_handler(OperationalMode newMode) {
        // Validate transition
        if (isValidTransition(this->m_mode, newMode)) {
            this->m_mode = newMode;
            this->log_ACTIVITY_HI_ModeChanged(newMode);
            this->tlmWrite_Mode(newMode);
        } else {
            this->log_WARNING_HI_InvalidTransition(this->m_mode, newMode);
        }
    }

private:
    bool isValidTransition(OperationalMode from, OperationalMode to) {
        // Define valid state transitions
        // ...
    }
};
```

### Pattern 2: State Machine with Entry/Exit Actions

```cpp
void MyComponent::transitionToMode(OperationalMode newMode) {
    // Exit current mode
    this->exitMode(this->m_mode);

    // Change state
    OperationalMode oldMode = this->m_mode;
    this->m_mode = newMode;

    // Enter new mode
    this->enterMode(this->m_mode);

    // Report transition
    this->log_ACTIVITY_HI_ModeTransition(oldMode, newMode);
    this->tlmWrite_Mode(newMode);
}

void MyComponent::enterMode(OperationalMode mode) {
    switch (mode) {
        case MODE_ACTIVE:
            // Start processing
            break;
        case MODE_SAFE:
            // Disable outputs
            break;
        // ...
    }
}

void MyComponent::exitMode(OperationalMode mode) {
    switch (mode) {
        case MODE_ACTIVE:
            // Stop processing
            break;
        // ...
    }
}
```

## State Persistence

### Pattern 1: Parameter-Based State

For state that should persist across reboots:

```fpp
# In component FPP
param LAST_MODE: U32 default 0
```

```cpp
void MyComponent::preamble() {
    // Restore state from parameter
    this->m_mode = static_cast<OperationalMode>(
        this->paramGet_LAST_MODE()
    );
}

void MyComponent::setMode_handler(OperationalMode newMode) {
    this->m_mode = newMode;
    // Persist to parameter
    this->paramSet_LAST_MODE(static_cast<U32>(newMode));
}
```

### Pattern 2: File-Based State

For complex state:

```cpp
void MyComponent::saveState() {
    // Serialize state to buffer
    Fw::SerializeBufferBase buffer;
    buffer.serialize(this->m_counter);
    buffer.serialize(this->m_value);
    // ...

    // Write to file
    Os::File file;
    file.open("/data/state.bin", Os::File::OPEN_WRITE);
    file.write(buffer.getBuffAddr(), buffer.getBuffLength());
    file.close();
}

void MyComponent::loadState() {
    // Read from file
    Os::File file;
    file.open("/data/state.bin", Os::File::OPEN_READ);
    U8 data[MAX_SIZE];
    NATIVE_INT_TYPE size;
    file.read(data, sizeof(data), size);
    file.close();

    // Deserialize state
    Fw::SerializeBufferBase buffer;
    buffer.setBuffData(data, size);
    buffer.deserialize(this->m_counter);
    buffer.deserialize(this->m_value);
    // ...
}
```

## Common State Management Pitfalls

**Pitfall 1: Forgetting thread safety in sync handlers**
```cpp
// BAD - sync handler on active component, no mutex
U32 getCount_handler() {
    return this->m_counter;  // Race with async handlers!
}
```

**Pitfall 2: Deadlock from nested locks**
```cpp
// BAD - calling sync port while holding mutex
void handler1() {
    this->m_mutex.lock();
    this->syncPort_out();  // May deadlock if syncPort calls back
    this->m_mutex.unlock();
}
```

**Pitfall 3: Uninitialized state**
```cpp
// BAD - forgot to initialize
U32 m_counter;  // Undefined value!

// GOOD - initialize in constructor
MyComponent::MyComponent(...) :
    m_counter(0)  // Initialized
{}
```

**Pitfall 4: State modified outside handlers**
```cpp
// BAD - modifying state in non-handler method
void MyComponent::someUtilityFunction() {
    this->m_counter++;  // Thread safety unclear
}
```

**How to apply:**
- Use async handlers for state-modifying operations (no mutex needed)
- Use guarded ports for sync handlers that access state
- Initialize all state in constructor or preamble()
- Document state transitions and valid states
- Use enums for mode/state variables (not raw integers)
- Consider state persistence for critical state
- Test state transitions thoroughly
- Avoid nested locks (deadlock risk)
- Keep critical sections short (mutex held briefly)
