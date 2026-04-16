---
name: F' Event (EVR) System Architecture
description: Event reporting system including Fw::Log ports and ActiveTextLogger component
type: reference
---

# F' Event (EVR) System Architecture

The F' event system provides logging of significant occurrences within the flight software. Events are also called EVRs (Event Reports) in some contexts.

## Event Severity Levels

F' defines seven event severity levels (from most to least severe):

| Severity | Description | Usage |
|----------|-------------|-------|
| **FATAL** | Fatal error, software cannot continue | System-critical failures |
| **WARNING_HI** | Serious failure, software can continue | Major component failures |
| **WARNING_LO** | Minor failure, software largely unaffected | Recoverable errors |
| **COMMAND** | Command-related activity | Command success/failure |
| **ACTIVITY_HI** | Important nominal event | Major state changes |
| **ACTIVITY_LO** | Unimportant nominal event (subset of HI) | Minor state changes |
| **DIAGNOSTIC** | Detailed debug events (normally not seen) | Debugging information |

## Event Port Types

### Fw::Log Port (Fw/Log/docs/sdd.md)

**Purpose:** Pass serialized form of an event

**Arguments:**
- `id` (FwEventIdType): Event identifier
- `timeTag` (Fw::Time): System time when event happened
- `severity` (enum): Event severity (see above)
- `args` (Fw::LogBuffer): Serialized event arguments

**Usage:** Binary event data, sent to ActiveLogger or event packetizer for downlink

### Fw::LogText Port (Fw/Log/docs/sdd.md)

**Purpose:** Pass printable text representation of an event

**Arguments:**
- `id` (FwEventIdType): Event identifier
- `timeTag` (Fw::Time): System time when event happened
- `severity` (enum): Text severity (TEXT_LOG_FATAL, etc.)
- `text` (Fw::TextLogString): Text description of event

**Usage:** Human-readable event output, sent to text loggers (console, file)

### Fw::LogBuffer Serializable

The `Fw::LogBuffer` class stores serialized event argument data. This allows the framework to handle events generically without knowing argument types at the framework level.

### Fw::LogStringArg

Used by the autocoder when string arguments are declared in events.

## Event Components

### Svc::ActiveTextLogger (Svc/ActiveTextLogger/docs/sdd.md)

**Purpose:** Process log text from components, write to stdout and optionally to file

**Requirements:**
- ISF-ATL-001: Print received log texts to standard output
- ISF-ATL-002: Write received log texts to optional file
- ISF-ATL-003: Format log text on calling thread, process on component's thread
- ISF-ATL-004: Stop writing to file if it would exceed max size
- ISF-ATL-005: Provide public method to supply filename and max size
- ISF-ATL-006: Attempt to create new file if supplied one exists (try "file0" through "file9", then overwrite original)

**Ports:**
- `TextLogger` (input, sync): Receives Fw::LogText events

**Key behaviors:**
- **Active component** with dedicated thread
- Formats text on caller's thread (ISR-safe)
- Performs file I/O on component's thread (prevents blocking callers)
- File rotation to prevent overwriting existing log files
- Enforces maximum file size limit

**Why:** By formatting on caller's thread but writing on component thread, ActiveTextLogger maintains consistent event ordering while preventing I/O operations from blocking critical paths.

## Event Flow Architecture

```
Component
  └── Event emission (auto-generated)
      ├── log_out (Fw::Log) → Binary event handler
      │     └── EventLogger / TlmPacketizer → Downlink
      └── logText_out (Fw::LogText) → Text event handler
            └── ActiveTextLogger → Console / File
```

**Key insight:** Events are sent to TWO separate paths:
1. Binary path (Fw::Log) for downlink/storage
2. Text path (Fw::LogText) for human-readable console output

Both paths can be connected simultaneously, or either can be omitted based on deployment needs.

## Event Definition Pattern

In component FPP:
```
event MY_EVENT(value: U32, status: string) \
    severity activity high \
    format "Operation completed with value {} and status {}"
```

In component C++:
```cpp
// Emit event
this->log_ACTIVITY_HI_MY_EVENT(value, status);
```

**Auto-generated code handles:**
- Serialization of arguments into Fw::LogBuffer
- Formatting into text string
- Calling both log_out and logText_out ports
- Including timestamp from time_out port

## Event Filtering and Throttling

Some F' systems implement event filtering/throttling components that:
- Reduce duplicate events
- Filter by severity level
- Limit event rate to prevent saturation

**How to apply:**
- Choose appropriate severity levels based on operational impact
- Use DIAGNOSTIC for debug events that normally shouldn't be seen
- Use FATAL only for truly unrecoverable conditions
- Format strings should be clear and include relevant values
- Keep event argument lists concise (serialization has size limits)
- Consider event downlink bandwidth when defining many events
