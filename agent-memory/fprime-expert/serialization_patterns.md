---
name: F' Serialization Patterns
description: Fw::Serializable base class, buffer management, and serialization patterns
type: feedback
---

# F' Serialization Patterns

F' uses serialization to convert typed data to/from byte streams for network transport, file storage, and port communication.

## Fw::Serializable Base Class

**Purpose:** Base class for all serializable types in F'

**Key methods:**
```cpp
// Serialize object into buffer
SerializeStatus serialize(SerializeBufferBase& buffer) const;

// Deserialize object from buffer
SerializeStatus deserialize(SerializeBufferBase& buffer);

// Get serialized size (in bytes)
U32 getSerializedSize() const;
```

**Return status (SerializeStatus enum):**
- `FW_SERIALIZE_OK` - Success
- `FW_SERIALIZE_FORMAT_ERROR` - Format error during deserialization
- `FW_SERIALIZE_NO_ROOM_LEFT` - Buffer too small for serialization
- `FW_DESERIALIZE_BUFFER_EMPTY` - No more data to deserialize
- `FW_DESERIALIZE_FORMAT_ERROR` - Deserialization format error
- `FW_DESERIALIZE_SIZE_MISMATCH` - Size mismatch error

## Buffer Classes

### SerializeBufferBase
Abstract base class for serialization buffers.

**Key methods:**
```cpp
SerializeStatus serialize(U8 val);      // Serialize primitive types
SerializeStatus serialize(U16 val);
SerializeStatus serialize(U32 val);
SerializeStatus serialize(U64 val);
SerializeStatus serialize(I8 val);
// ... etc for all primitive types

SerializeStatus deserialize(U8& val);   // Deserialize primitive types
SerializeStatus deserialize(U16& val);
// ... etc

void reset();                           // Reset for serialization
void resetForDeser();                   // Reset for deserialization
```

### Common Buffer Types

**Fw::ComBuffer** - Communication buffer (Fw/Com)
- Used for command/telemetry/event packets
- Typical size: 256-2048 bytes

**Fw::CmdArgBuffer** - Command argument buffer (Fw/Cmd)
- Stores serialized command arguments
- Auto-sized based on command definitions

**Fw::LogBuffer** - Event argument buffer (Fw/Log)
- Stores serialized event arguments
- Auto-sized based on event definitions

**Fw::TlmBuffer** - Telemetry value buffer (Fw/Tlm)
- Stores serialized telemetry channel value
- Auto-sized based on channel type

**Fw::PrmBuffer** - Parameter value buffer (Fw/Prm)
- Stores serialized parameter value
- Auto-sized based on parameter type

## Serialization Patterns

### Pattern 1: Framework-Generated Serialization

For commands, events, telemetry, parameters - **serialization is automatic**:

```cpp
// Command handler - arguments already deserialized
void MyComponent::MY_CMD_cmdHandler(
    FwOpcodeType opCode,
    U32 cmdSeq,
    U32 arg1,           // Primitive automatically deserialized
    F32 arg2,           // Primitive automatically deserialized
    const Fw::CmdStringArg& arg3  // String automatically deserialized
) {
    // Use arguments directly
}

// Telemetry write - value automatically serialized
this->tlmWrite_MY_CHANNEL(myValue);

// Event emission - arguments automatically serialized
this->log_WARNING_HI_MY_EVENT(arg1, arg2, arg3);
```

**Why:** F' autocoder generates serialization code based on FPP definitions. User doesn't write serialization code for standard framework features.

### Pattern 2: Custom Port Serialization

For custom port types with complex arguments:

```fpp
# Define port type with complex argument
port MyPort(
    timestamp: Fw.Time,
    value: F64,
    status: MyStatusEnum
)
```

Auto-generated port code handles serialization when port is async.

### Pattern 3: Manual Serialization for Custom Types

For custom data structures sent via ports or stored in files:

```cpp
class MyData : public Fw::Serializable {
public:
    U32 counter;
    F64 value;
    MyEnum status;

    // Serialize this object
    SerializeStatus serialize(SerializeBufferBase& buffer) const override {
        SerializeStatus stat;

        stat = buffer.serialize(this->counter);
        if (stat != FW_SERIALIZE_OK) return stat;

        stat = buffer.serialize(this->value);
        if (stat != FW_SERIALIZE_OK) return stat;

        stat = buffer.serialize(static_cast<I32>(this->status));
        if (stat != FW_SERIALIZE_OK) return stat;

        return FW_SERIALIZE_OK;
    }

    // Deserialize this object
    SerializeStatus deserialize(SerializeBufferBase& buffer) override {
        SerializeStatus stat;

        stat = buffer.deserialize(this->counter);
        if (stat != FW_SERIALIZE_OK) return stat;

        stat = buffer.deserialize(this->value);
        if (stat != FW_SERIALIZE_OK) return stat;

        I32 statusVal;
        stat = buffer.deserialize(statusVal);
        if (stat != FW_SERIALIZE_OK) return stat;
        this->status = static_cast<MyEnum>(statusVal);

        return FW_SERIALIZE_OK;
    }

    // Return serialized size
    U32 getSerializedSize() const override {
        return sizeof(U32) +      // counter
               sizeof(F64) +      // value
               sizeof(I32);       // status
    }
};
```

### Pattern 4: Array Serialization

**Fixed-size arrays:**
```cpp
U32 data[10];
for (U32 i = 0; i < 10; i++) {
    stat = buffer.serialize(data[i]);
    if (stat != FW_SERIALIZE_OK) return stat;
}
```

**Variable-size arrays:**
```cpp
U32 count;  // Number of elements
U32 data[MAX_SIZE];

// Serialize count first, then elements
stat = buffer.serialize(count);
if (stat != FW_SERIALIZE_OK) return stat;

for (U32 i = 0; i < count; i++) {
    stat = buffer.serialize(data[i]);
    if (stat != FW_SERIALIZE_OK) return stat;
}
```

### Pattern 5: String Serialization

F' has built-in string types:

**Fw::String** - Base string class
**Fw::CmdStringArg** - Command string argument
**Fw::LogStringArg** - Event string argument

Strings are serialized as:
1. Length (U16 or U32)
2. Character data (no null terminator)

Auto-generated when used in commands/events/telemetry.

## Endianness

F' serializes all data in **big-endian** (network byte order).

**Why:** Standardizes byte order across different processor architectures. Ground system and flight system may have different native endianness.

**How it works:**
- `SerializeBufferBase` automatically handles byte swapping
- Transparent to user code
- Files written by one architecture can be read by another

## Buffer Management Best Practices

**Buffer sizing:**
- Size buffers to hold maximum expected data
- Use `getSerializedSize()` to pre-calculate required space
- Check return status to detect buffer overflow

**Error handling:**
```cpp
SerializeStatus stat = buffer.serialize(myData);
if (stat != FW_SERIALIZE_OK) {
    // Handle error - log, return error status, etc.
    return stat;
}
```

**Buffer reset:**
- Before serializing: `buffer.reset()`
- Before deserializing: `buffer.resetForDeser()`

**Versioning:**
For custom serializable types that may evolve:

```cpp
SerializeStatus serialize(SerializeBufferBase& buffer) const override {
    // Write version first
    buffer.serialize(static_cast<U8>(VERSION));

    // Write data
    buffer.serialize(field1);
    buffer.serialize(field2);
    // ...
}

SerializeStatus deserialize(SerializeBufferBase& buffer) override {
    U8 version;
    buffer.deserialize(version);

    if (version == 1) {
        // Deserialize version 1 format
    } else if (version == 2) {
        // Deserialize version 2 format
    } else {
        return FW_DESERIALIZE_FORMAT_ERROR;
    }
}
```

## Common Serialization Pitfalls

**Pitfall 1: Forgetting to check return status**
```cpp
// BAD - doesn't check status
buffer.serialize(data1);
buffer.serialize(data2);  // May fail if buffer full

// GOOD - checks each status
stat = buffer.serialize(data1);
if (stat != FW_SERIALIZE_OK) return stat;
stat = buffer.serialize(data2);
if (stat != FW_SERIALIZE_OK) return stat;
```

**Pitfall 2: Mismatched serialize/deserialize order**
```cpp
// Serialize
buffer.serialize(field1);
buffer.serialize(field2);

// Deserialize - WRONG ORDER
buffer.deserialize(field2);  // Gets field1 data!
buffer.deserialize(field1);  // Gets field2 data!
```

**Pitfall 3: Not resetting buffer**
```cpp
// BAD - buffer may have stale data
buffer.serialize(newData);

// GOOD - reset first
buffer.reset();
buffer.serialize(newData);
```

**Pitfall 4: Size calculation errors**
```cpp
// BAD - wrong size
U32 getSerializedSize() const override {
    return sizeof(MyStruct);  // Wrong if struct has padding
}

// GOOD - sum of serialized field sizes
U32 getSerializedSize() const override {
    return sizeof(U32) + sizeof(F64) + ...;
}
```

## Serialization Performance

**Buffer copying:** Minimize copies
- Pass buffers by reference
- Use move semantics when possible

**Large data:** For very large data structures:
- Consider chunking (serialize in multiple packets)
- Use file transfer for bulk data

**Validation:** Balance validation with performance
- Validate critical fields (enum ranges, array sizes)
- Skip validation in performance-critical paths if data source is trusted

**How to apply:**
- Use framework-generated serialization for commands/events/telemetry (don't reinvent)
- Derive from Fw::Serializable for custom data structures
- Always check serialization return status
- Match serialize/deserialize order exactly
- Use versioning for long-lived data formats (files, persistent storage)
- Test serialization with boundary cases (empty arrays, max sizes, etc.)
