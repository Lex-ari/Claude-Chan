---
name: F Prime Health Component Ping Monitoring System
description: Health component ping mechanism, timeout tracking, watchdog stroking, and failure detection
type: reference
---

# Svc::Health Component Monitoring System

## Location
- SDD: `fprime/Svc/Health/docs/sdd.md`
- FPP: `fprime/Svc/Health/Health.fpp`

## Purpose
Monitors execution health of active components by pinging them and checking for responses within timeout thresholds.

## Component Type
**Queued component** - Has message queue but no dedicated thread (passive-like, but with queue)

## Key Ports

### Input Ports
- `Run: Svc.Sched (sync input)` - Periodic call to execute health checks
- `PingReturn[N]: Svc.Ping (async input)` - Receives ping responses from components

### Output Ports
- `PingSend[N]: Svc.Ping` - Sends ping requests to components
- `WdogStroke: Svc.WatchDog` - Strokes watchdog when all components healthy

### Port Matching
`match PingSend with PingReturn` - Port numbers must correspond

## Ping Port Type (Svc.Ping)

**Definition:**
```fpp
port Ping(
    key: U32  // Ping key value to return
)
```

**Protocol:**
1. Health sends ping with `key` value
2. Component echoes `key` back on return port
3. Health validates `key` matches expected value

## Ping Table Structure

**Configured at initialization via `setPingEntries()`**

**Entry Structure:**
```cpp
struct PingEntry {
    string name;              // Component name (for events)
    U32 warnThreshold;        // Cycles before warning event
    U32 fatalThreshold;       // Cycles before FATAL event
    U32 counter;              // Current countdown counter
    bool enabled;             // Ping entry is enabled
    PingStatus status;        // Current status
};
```

**PingStatus enum:**
- `IDLE` - No outstanding ping
- `WAITING` - Ping sent, waiting for response
- `WARNING` - Warning threshold exceeded
- `FATAL` - Fatal threshold exceeded

## Health Check Flow (Run Handler)

**Handler:** `Run_handler(portNum)`

**Called by:** Rate group (typically 1 Hz)

**Algorithm:**

1. **If health monitoring disabled:** Return immediately

2. **For each ping entry:**

   **If entry disabled:** Skip

   **If status == IDLE:**
   - Send ping: `PingSend_out(portNum, m_key)`
   - Set status to `WAITING`
   - Set counter to `fatalThreshold`

   **If status == WAITING:**
   - Decrement `counter`
   - If `counter == warnThreshold`:
     - Emit `HLTH_PING_WARN` event
     - Set status to `WARNING`
     - Increment `PingLateWarnings` telemetry
   - If `counter == 0`:
     - Emit `HLTH_PING_LATE` **FATAL** event
     - Set status to `FATAL`
     - **Do NOT stroke watchdog**

   **If status == WARNING:**
   - Continue decrementing counter
   - If `counter == 0`:
     - Emit `HLTH_PING_LATE` FATAL event
     - Set status to `FATAL`

   **If status == FATAL:**
   - Component has failed, stop pinging

3. **Stroke watchdog:**
   - Only if ALL enabled components responded in time
   - Call `WdogStroke_out()`

## Ping Response Flow

**Handler:** `PingReturn_handler(portNum, key)`

**Triggered by:** Component returning ping

**Algorithm:**

1. **Validate key:**
   ```cpp
   if (key != m_key) {
       log_FATAL_HLTH_PING_WRONG_KEY(entry.name, key);
       entry.status = FATAL;
       return;
   }
   ```

2. **Update entry:**
   ```cpp
   entry.status = IDLE;
   entry.counter = 0;
   ```

3. **Result:** Entry ready for next ping cycle

## Commands

### HLTH_ENABLE
```fpp
async command HLTH_ENABLE(enable: Fw.Enabled)
```

**Purpose:** Enable or disable all health monitoring

**Effect:** Sets global flag, stops all pinging when disabled

### HLTH_PING_ENABLE
```fpp
async command HLTH_PING_ENABLE(entry: string, enable: Fw.Enabled)
```

**Purpose:** Enable or disable monitoring for specific entry

**Effect:** Sets `enabled` flag for named entry

### HLTH_CHNG_PING
```fpp
async command HLTH_CHNG_PING(
    entry: string,
    warningValue: U32,
    fatalValue: U32
)
```

**Purpose:** Update timeout thresholds for entry

**Validation:** `fatalValue > warningValue`

**Effect:** Updates thresholds, emits `HLTH_PING_UPDATED` event

## Active Component Ping Pattern

**Component Side (typical implementation):**

```cpp
void Component::pingIn_handler(FwIndexType portNum, U32 key) {
    // Execute on component's thread (async port)
    // Immediately return key
    this->pingOut_out(0, key);
}
```

**Key Requirement:** Handler must execute on component's thread

**Why:** Verifies thread is alive and processing messages

**Port Configuration:**
- `pingIn` declared as **async input** (queued)
- `pingOut` output port
- Connected to Health component

## Watchdog Stroking

**Condition:** Stroke watchdog ONLY if all enabled components responded in time

**Effect:** Prevents system reset if all components healthy

**Missing Stroke:** If any component fails to respond → watchdog not stroked → system reset

**Integration:** Watchdog component (external) expects periodic strokes

## Events

### HLTH_PING_WARN
- **Severity:** WARNING_HIGH
- **Meaning:** Component response time exceeds warning threshold
- **Action:** Investigate performance, may recover

### HLTH_PING_LATE
- **Severity:** FATAL
- **Meaning:** Component failed to respond within fatal threshold
- **Action:** Component is dead or severely blocked

### HLTH_PING_WRONG_KEY
- **Severity:** FATAL
- **Meaning:** Component returned wrong key value
- **Action:** Component corruption or connection error

## Telemetry

### PingLateWarnings
- **Type:** U32
- **Meaning:** Cumulative count of warning threshold exceedances
- **Use:** Track component health trends

## Critical Design Patterns

### 1. Key-Based Response Validation
- Each ping has unique key
- Prevents accepting stale responses
- Detects component state corruption

### 2. Two-Tier Threshold System
- Warning threshold: Early alert
- Fatal threshold: Critical failure
- Allows progressive response to degradation

### 3. Countdown Counter Mechanism
- Counter initialized to fatal threshold
- Decremented each cycle
- Hitting warning → event
- Hitting zero → FATAL

### 4. Watchdog Integration
- Health acts as watchdog feeder
- Only strokes if all components healthy
- Provides system-level liveness check

### 5. Per-Entry Enable/Disable
- Can disable monitoring for specific components
- Useful during development or when component intentionally stopped
- Global enable/disable for all monitoring

### 6. Run on Caller's Thread (Sync Input)
- `Run` port is sync, not async
- Executes on rate group's thread
- Minimal latency for health checks
- No queuing delay

### 7. Async Ping Return
- `PingReturn` is async (queued)
- Components can respond asynchronously
- Health queues responses for processing

## Typical Topology Integration

```cpp
// Health component configuration
Health::PingEntry pingTable[] = {
    {"component1", 3, 5},  // Warn at 3 cycles, fatal at 5
    {"component2", 3, 5},
    ...
};
health.setPingEntries(pingTable, numEntries);

// Connections
rateGroup1Hz.out → health.Run
health.PingSend[0] → component1.pingIn
component1.pingOut → health.PingReturn[0]
health.PingSend[1] → component2.pingIn
component2.pingOut → health.PingReturn[1]
health.WdogStroke → watchdog.stroke
```

## Common Issues and Debugging

### Component Not Responding
1. Check if component thread is alive
2. Check if component queue is full
3. Check if pingIn handler is connected and implemented
4. Check if component is blocked in handler

### Wrong Key Events
1. Check for connection errors in topology
2. Check for component memory corruption
3. Verify component returns same key it receives

### Excessive Warnings
1. Increase warning threshold
2. Check component performance (may be overloaded)
3. Consider splitting component work across rate groups

### Watchdog Not Stroked
1. Check if all components enabled
2. Check if any component in WARNING or FATAL state
3. Verify WdogStroke port is connected

**How to apply:** When adding new active component:
1. Add ping ports to component FPP (async input, output)
2. Implement ping handler to echo key
3. Add entry to health ping table
4. Connect to Health component
5. Set appropriate thresholds based on expected latency
