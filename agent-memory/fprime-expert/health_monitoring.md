---
name: F' Health Monitoring System
description: Component health monitoring using Svc::Health and ping mechanism
type: reference
---

# F' Health Monitoring System

F' provides a health monitoring system to detect unresponsive or hung components using a ping mechanism.

## Svc::Health Component (Svc/Health/docs/sdd.md)

**Purpose:** Monitor execution health of software by pinging active components and checking for responses

**Requirements:**
- HTH-001: Ping each output port specified in table
- HTH-002: Track timeout cycles for each component
- HTH-003: Issue FATAL event if component fails to return ping by timeout
- HTH-004: Command to enable/disable all monitoring
- HTH-005: Command to enable/disable monitoring for particular port
- HTH-006: Command to update ping timeout values for port
- HTH-007: Stroke watchdog port while all ping replies within limit

**Ports:**
- `PingSend` (output): Send ping requests to components (Svc::Ping)
- `PingReturn` (input, async): Receive ping responses from components (Svc::Ping)
- `Run` (input, sync): Execute periodic behavior (Svc::Sched)
- `Wdog` (output): Stroke watchdog (Svc::WatchDog)

**Commands:**
- **HLTH_ENABLE:** Enable all health monitoring
- **HLTH_DISABLE:** Disable all health monitoring
- **HLTH_ENABLE_PORT:** Enable monitoring for specific port
- **HLTH_DISABLE_PORT:** Disable monitoring for specific port
- **HLTH_PING_UPDATE_TIMEOUT:** Update timeout value for port

## Health Monitoring Mechanism

### Ping Table
Health component maintains a table of monitored components:

| Field | Description |
|-------|-------------|
| Port number | Output port index for PingSend |
| Timeout | Max allowed cycles without response (# of Run calls) |
| Counter | Current countdown to timeout |
| Enabled | Whether monitoring is enabled for this entry |
| Status | Pending response or idle |

### Monitoring Cycle (Run Port Handler)

For each enabled table entry:

1. **If idle (no pending ping):**
   - Call PingSend[portNum] with key (ping counter value)
   - Set status to "pending"
   - Set counter to timeout value

2. **If pending response:**
   - Decrement counter
   - If counter reaches warning threshold: Emit warning event & telemetry
   - If counter reaches zero (timeout): Emit FATAL event
   - If response received: Reset to idle

3. **Stroke watchdog:**
   - If ALL pings within limits: Call Wdog port
   - If ANY ping timed out: Do NOT stroke watchdog

### Ping Key
Health component uses an incrementing counter as the "key":
- Counter incremented each Run cycle
- Sent to component via PingSend
- Component must return same key via PingReturn
- Mismatch indicates lost or duplicate response

## Svc::Ping Port (Svc/Ping/docs/sdd.md)

**Purpose:** Port type for health check pings

**Arguments:**
- `key` (U32): Ping key/counter value

**Usage in component:**
```cpp
void MyComponent::pingIn_handler(NATIVE_INT_TYPE portNum, U32 key) {
    // Echo back the key
    this->pingOut_out(portNum, key);
}
```

**Critical requirement:** Ping handler MUST execute on component's thread (async input port). This ensures the thread is alive and dispatching messages.

## Health Monitoring Flow

```
RateGroup (e.g., 1Hz)
  └─> Health::Run
      └─> For each monitored component:
          ├─> PingSend(key) → Component::pingIn
          │     └─> Component thread dispatches ping handler
          │           └─> PingReturn(key) → Health::PingReturn
          │                 └─> Health marks ping received
          └─> Check timeout counters
              └─> If timeout: Emit FATAL event
```

**Key insight:** Because ping handlers execute on component's thread (via async input port), a timeout indicates either:
1. Component thread is hung or crashed
2. Component's message queue is full or stuck
3. Component is not dispatching messages

## Timeout Configuration

**Wall time calculation:**
```
Wall time = timeout_cycles × Run_period
```

**Example:**
- Run port called at 1Hz (period = 1 second)
- Timeout = 5 cycles
- Wall time = 5 seconds

**Threshold types:**
- **Warning threshold:** Emit warning but continue monitoring
- **Fault threshold (timeout):** Emit FATAL event

**Typical values:**
- Fast components: 2-5 cycles (2-5 seconds at 1Hz)
- Slow components: 10-30 cycles (10-30 seconds at 1Hz)
- Critical components: Lower timeout (detect issues quickly)
- Non-critical components: Higher timeout (avoid false alarms)

## Watchdog Integration

**Purpose:** External watchdog timer that resets system if not stroked

**Flow:**
1. Health component monitors all pings
2. If ALL pings received within timeout: Stroke Wdog port
3. If ANY ping times out: Do NOT stroke Wdog port
4. External watchdog not stroked → system reset

**Why:** Provides hardware-level protection against software hangs. If health monitoring itself fails, watchdog will still reset the system.

**Typical watchdog timeout:** Longer than longest health timeout (e.g., 60 seconds if max health timeout is 30 seconds).

## Health Monitoring Best Practices

**What to monitor:**
- Active components only (passive components have no thread)
- Critical flight software components
- Components with complex logic prone to hangs
- Components interacting with external hardware

**What NOT to monitor:**
- Passive components (no thread to check)
- Simple utility components
- Components with infrequent operation (may timeout during idle)

**Timeout tuning:**
- Start with conservative (long) timeouts during development
- Tighten timeouts based on measured execution time
- Account for worst-case load and priority inversion
- Add margin for jitter and system load

**False alarm prevention:**
- Don't set timeouts too aggressively
- Consider priority inversion scenarios (high-priority tasks blocking)
- Monitor warning events to detect degrading performance before timeout
- Use telemetry to track health counter values

**Testing:**
- Verify ping mechanism during integration testing
- Inject faults (hang component) to verify timeout detection
- Test watchdog reset mechanism (in controlled environment)
- Verify health disable commands work (for troubleshooting)

**Operational use:**
- Monitor health events and telemetry
- Investigate warning events proactively
- Disable monitoring only temporarily for debugging
- Update timeout values if component behavior changes
- Document health timeout rationale

**How to apply:**
- Include Health component in every flight deployment
- Connect all active components to health monitoring
- Configure timeouts based on component execution characteristics
- Integrate with external hardware watchdog for system-level protection
- Use health disable commands sparingly (debugging only)
- Monitor health telemetry for trends (increasing timeout counters)
- Have procedures for handling health timeout events (component restart, failover, etc.)
