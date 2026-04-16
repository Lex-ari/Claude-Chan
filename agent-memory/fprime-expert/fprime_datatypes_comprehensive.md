---
name: F Prime Data Types Comprehensive
description: Primitive types, enums, arrays, serializables, polymorphic types, and type system
type: reference
---

# F Prime Data Types Comprehensive

## Primitive Types

F Prime provides exact-width type names to ensure portability across architectures.

| F Prime Type | C/C++ Type | Bits | Description |
|--------------|------------|------|-------------|
| BOOL | bool | — | C++ boolean |
| I8 | int8_t | 8 | Signed integer |
| I16 | int16_t | 16 | Signed integer |
| I32 | int32_t | 32 | Signed integer |
| I64 | int64_t | 64 | Signed integer |
| U8 | uint8_t | 8 | Unsigned integer |
| U16 | uint16_t | 16 | Unsigned integer |
| U32 | uint32_t | 32 | Unsigned integer |
| U64 | uint64_t | 64 | Unsigned integer |
| F32 | float | 32 | Floating point |
| F64 | double | 64 | Floating point |

**Source:** Types from `stdint.h` and `stdbool.h`

**Platform support:** Not all platforms support all types. See [Configuring F Prime: Architecture Supported Primitive Types] for platform-specific configuration.

**Why:** Ensures consistent size across different architectures. `int` might be 16-bit or 32-bit depending on platform; `I32` is always 32-bit.

## Polymorphic Type (PolyType)

Single type that can store any primitive type value.

**Setting values:**
```cpp
PolyType myInt(123);
PolyType myFloat;
myFloat = 123.03;
```

**Getting values (two methods):**
```cpp
// Method 1: Cast
U32 val = (U32)pt;

// Method 2: get()
U32 val;
pt.get(val);
```

**Both methods assert if type mismatch.**

**Checking type:**
```cpp
PolyType p(123);
if (p.isU32()) {
    U32 val = (U32)p;
}
```

**Use case:** Generic value storage (e.g., PolyDb component stores PolyType entries)

## Enums

Autocoded enumeration types with convenience functions.

**FPP definition:**
```fpp
enum Status {
    OK = 0
    ERROR = 1
    PENDING = 2
}
```

**Generated C++ class:**
- Stores as integer type internally
- Type-safe wrapper with named constants
- Can serialize/deserialize for ports, commands, events, telemetry
- Works with ground system automatically

**Use in C++:**
```cpp
Status s = Status::OK;
if (s == Status::ERROR) { /* ... */ }
```

**Why autocoded:** Ground system needs enum definitions. Autocode ensures consistency between FSW and ground.

## Arrays

Fixed-length, type-homogeneous containers.

**FPP definition:**
```fpp
array FloatArray = [10] F32
```

**Properties:**
- Fixed length (defined at design time)
- All elements same type
- Can contain primitives or complex types
- Serializable for ports, commands, events, telemetry

**Use in C++:**
Autocoded array class with accessors, size methods, serialization support.

**Use case:** Fixed-size data collections (e.g., sensor readings array, coefficient array)

## Serializables (Structs)

Field-value compositions, like C++ `struct` but autocoded with serialization.

**FPP definition:**
```fpp
struct SensorReading {
    timestamp: U64
    temperature: F32
    pressure: F32
    valid: bool
}
```

**Generated C++ class:**
- Field accessor methods
- Serialize/deserialize methods
- Can be used in ports, commands, events, telemetry
- Ground system automatically understands structure

**Use in C++:**
```cpp
SensorReading reading;
reading.setTimestamp(12345);
reading.setTemperature(25.3);
F32 temp = reading.getTemperature();
```

**Why:** Type-heterogeneous compositions. Arrays are homogeneous, serializables are heterogeneous.

## Alias Types

Alternate name for existing type.

**FPP definition:**
```fpp
type Temperature = F32
```

**Use case:** Semantic clarity. `Temperature` is more meaningful than `F32`.

## C++ Classes (Manual Serializables)

For software-only use (not in FPP, not with ground system), can use arbitrary C++ classes.

**Requirements for port arguments:**
Must inherit from `Fw::Serializable` and implement:

```cpp
Fw::SerializeStatus serializeTo(
    Fw::SerialBufferBase& buffer,
    Fw::Endianness mode = Fw::Endianness::BIG
) const;

Fw::SerializeStatus deserializeFrom(
    Fw::SerialBufferBase& buffer,
    Fw::Endianness mode = Fw::Endianness::BIG
);
```

**Buffer interface:** `Fw::SerialBufferBase` is abstract interface. Concrete implementations:
- `Fw::SerializeBufferBase`
- `Fw::ExternalSerializeBufferWithMemberCopy`

**Endianness:**
- Default: `Fw::Endianness::BIG` (network byte order)
- Can specify `Fw::Endianness::LITTLE` for little-endian

**Use case:** Complex internal data structures not needed by ground system.

## String Types

F Prime has string support for ports, commands, events, parameters.

**In FPP:**
```fpp
string
```

**In C++:**
Represented as `Fw::StringBase` or subclasses:
- `Fw::InternalString<size>`: Fixed internal buffer
- `Fw::ExternalString`: External buffer reference

**Port parameter:** Passed as `const Fw::StringBase&` to avoid copying.

**Use case:** Text parameters, log messages, file names.

## Time Type

**FPP:**
```fpp
Fw.Time
```

**C++ class:** `Fw::Time`

**Fields:**
- Seconds
- Microseconds (or nanoseconds depending on configuration)
- Time base (processor time, UTC, custom)

**Use:** Automatically added to events and telemetry. Can be used manually in ports/commands.

## Buffer Type

**FPP:**
```fpp
Fw.Buffer
```

**C++ class:** `Fw::Buffer`

**Purpose:** Generic data buffer container

**Fields:**
- Data pointer
- Size
- Context (optional metadata)

**Common use cases:**
- File transfer packets
- Communication packets
- Large data passing between components
- BufferManager allocations

## Type Usage Guidelines

### For Ground-Visible Data (Commands, Events, Telemetry)
**Use:** FPP-defined types (primitives, enums, arrays, serializables)
**Why:** Ground system automatically understands these types.

### For Software-Internal Port Arguments
**Use:** FPP types OR C++ classes inheriting from `Fw::Serializable`
**Why:** Flexibility for complex internal types not needed by ground.

### For Local Variables / Component State
**Use:** Any C++ type
**Why:** Not crossing component boundary, no serialization needed.

### For Large Data Transfer
**Use:** `Fw::Buffer` with buffer pool pattern
**Why:** Efficient memory management, can pass ownership between components.

## Type Availability

| Context | Available Types |
|---------|----------------|
| Port arguments | All FPP types, Fw::Buffer, custom Fw::Serializable |
| Command arguments | All FPP types |
| Event arguments | All FPP types |
| Telemetry channel type | All FPP types |
| Parameter type | All FPP types |
| Component member variables | All C++ types |
| Local variables | All C++ types |

## Serialization Notes

**Automatic serialization:** All FPP-defined types automatically serialize for:
- Port calls (when crossing serialization boundary)
- Commands (from ground to FSW)
- Events (from FSW to ground)
- Telemetry (from FSW to ground)
- Parameters (to/from parameter database)

**Manual serialization:** Only needed for custom C++ classes used as port arguments.

**Endianness:** Framework handles endianness conversion automatically for cross-platform compatibility.

## How to apply

1. **Use F Prime primitive types:** Always use `U32` not `unsigned int`, `I32` not `int`, etc.
2. **FPP for ground-visible:** Any data sent to/from ground should be FPP-defined type
3. **Enums over magic numbers:** Define enums for state machines, status codes, modes
4. **Serializables for structured data:** Group related fields into struct, not separate parameters
5. **Arrays for fixed collections:** Known-size collections (calibration tables, buffers)
6. **Alias for semantics:** Use type aliases to make intent clear (`type Temperature = F32`)
7. **Fw::Buffer for large data:** Don't pass large arrays by value, use buffers
8. **PolyType for generic storage:** When need to store different types in same container
9. **Manual serializable for complex internal:** If ground doesn't need to see it, can use custom C++ class
10. **Check platform support:** Verify target platform supports types you use (especially I64/U64)
