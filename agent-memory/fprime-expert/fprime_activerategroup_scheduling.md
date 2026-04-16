---
name: F Prime ActiveRateGroup Scheduling Mechanism
description: How ActiveRateGroup provides periodic execution scheduling with cycle slip detection
type: reference
---

# Svc::ActiveRateGroup Scheduling Mechanism

## Location
- SDD: `fprime/Svc/ActiveRateGroup/docs/sdd.md`
- FPP: `fprime/Svc/ActiveRateGroup/ActiveRateGroup.fpp`
- Implementation: `fprime/Svc/ActiveRateGroup/ActiveRateGroup.hpp/cpp`

## Purpose
Active component that drives periodic execution of other components connected to its output ports.

## Component Type
**Active component** - Has own thread and message queue

## Key Ports

### Input Ports
- `CycleIn: Svc.Cycle (async input, drop)` - Triggers one rate group cycle
- `PingIn: Svc.Ping (async input)` - Health monitoring

### Output Ports
- `RateGroupMemberOut[N]: Sched` - Calls each rate group member in order

**Port Attribute:** `drop` on `CycleIn` means message is dropped if queue is full (no blocking)

## Internal State

```cpp
U32 m_cycles;                          // Total cycles executed
U32 m_maxTime;                         // Maximum execution time (microseconds)
volatile bool m_cycleStarted;          // Flag indicating cycle started
U32 m_contexts[CONNECTION_COUNT_MAX];  // Context values for each output port
FwIndexType m_numContexts;             // Number of configured contexts
FwIndexType m_overrunThrottle;         // Throttle counter for overrun events
U32 m_cycleSlips;                      // Total cycle slips detected
```

## Configuration

**Method:** `configure(U32 contexts[], FwIndexType numContexts)`

**Purpose:** Set context values passed to each rate group member

**Context Values:**
- Array indexed by output port number
- Passed as argument to `Sched` port call
- Allows components to discriminate between multiple rate group calls

**Assertions:**
- `numContexts` must equal number of output ports
- Must be called before component starts

## Cycle Execution Flow

### Pre-Message Hook
**Handler:** `CycleIn_preMsgHook(portNum, cycleStart)`

**Execution:** Runs on **caller's thread** (before message queued)

**Purpose:** Set `m_cycleStarted = true` flag

**Why:** Detects if new cycle starts before previous completes (cycle slip)

### Message Handler
**Handler:** `CycleIn_handler(portNum, cycleStart)`

**Execution:** Runs on **component's thread** (after message dequeued)

**Algorithm:**

1. **Clear cycle flag:**
   ```cpp
   m_cycleStarted = false;
   ```

2. **Invoke all rate group members:**
   ```cpp
   for (port = 0; port < m_numContexts; port++) {
       if (isConnected_RateGroupMemberOut_OutputPort(port)) {
           RateGroupMemberOut_out(port, m_contexts[port]);
       }
   }
   ```
   - Calls are **synchronous** (blocking)
   - Members execute in sequence on ActiveRateGroup's thread
   - Context value determines what each member should do

3. **Measure cycle time:**
   ```cpp
   endTime.now();
   endTime.getDiffUsec(cycleStart, cycleTime);
   ```
   - `cycleStart` provided by cycle driver (e.g., RateGroupDriver)
   - Measures total time to execute all members

4. **Update maximum time:**
   ```cpp
   if (cycleTime > m_maxTime) {
       m_maxTime = cycleTime;
   }
   tlmWrite_RgMaxTime(m_maxTime);
   ```

5. **Check for cycle slip:**
   ```cpp
   if (m_cycleStarted) {  // Flag was set again by pre-message hook
       m_cycleSlips++;
       if (m_overrunThrottle < ACTIVE_RATE_GROUP_OVERRUN_THROTTLE) {
           log_WARNING_HI_RateGroupCycleSlip(m_cycles);
           m_overrunThrottle++;
       }
       tlmWrite_RgCycleSlips(m_cycleSlips);
   } else {  // No slip, decrement throttle
       if (m_overrunThrottle > 0) {
           m_overrunThrottle--;
       }
   }
   ```

6. **Increment cycle counter:**
   ```cpp
   m_cycles++;
   ```

## Cycle Slip Detection Mechanism

**Concept:** If new cycle message arrives before previous cycle completes, it's an overrun

**Implementation:**
1. Pre-message hook (on caller thread) sets `m_cycleStarted = true`
2. Message handler (on component thread) clears `m_cycleStarted = false`
3. Handler executes all rate group members (synchronous, blocking)
4. If `m_cycleStarted` is true again at end, means new cycle started during execution
5. Result: Previous cycle took too long → cycle slip

**Why Two Steps:**
- Pre-message hook detects new cycle arrival immediately
- Message handler can't detect it otherwise (queue might be empty by time it checks)

## Throttling

**Purpose:** Prevent event flooding during sustained overruns

**Mechanism:**
- `m_overrunThrottle` counter
- Increment on each overrun (up to `ACTIVE_RATE_GROUP_OVERRUN_THROTTLE`)
- Decrement on each successful cycle
- Only emit event if counter below threshold

**Configuration:** `ACTIVE_RATE_GROUP_OVERRUN_THROTTLE` in `config/ActiveRateGroupCfg.hpp`

## Telemetry

- `RgMaxTime` - Maximum cycle execution time (microseconds), update on change
- `RgCycleSlips` - Total cycle slips, update on change

## Preamble

**Method:** `preamble()`

**Called:** Before task enters message dispatch loop

**Action:** Emit `RateGroupStarted` diagnostic event

## Critical Design Patterns

### 1. Synchronous Member Execution
- All rate group members execute sequentially on ActiveRateGroup's thread
- Not parallel execution
- Order determined by port connection order
- Simplifies timing analysis (no race conditions between members)

### 2. Context Array Pattern
- Allows components to be called multiple times with different contexts
- Example: Same component called in 1Hz and 10Hz rate groups
- Component uses context to determine behavior

### 3. Pre-Message Hook for Overrun Detection
- Uses two-step flag mechanism
- Pre-message hook executes before queuing (on caller thread)
- Handler executes after dequeuing (on component thread)
- Flag state at end of handler indicates if new cycle arrived during execution

### 4. Drop Semantic on Input Port
- `async input port CycleIn: Svc.Cycle drop`
- If queue full, new cycle is dropped (no blocking)
- Prevents cycle driver from blocking
- ActiveRateGroup detects this as cycle slip

### 5. Throttled Event Emission
- Sustained overruns don't flood event log
- Counter mechanism provides hysteresis
- Still captures all slips in telemetry

## Common Usage Pattern

```cpp
// In topology initialization:
U32 rateGroupContext[] = {0, 0, 0, ...};  // One per output port
activeRateGroup.configure(rateGroupContext, numPorts);

// Connections:
rateGroupDriver.out → activeRateGroup.CycleIn
activeRateGroup.RateGroupMemberOut[0] → component1.schedIn
activeRateGroup.RateGroupMemberOut[1] → component2.schedIn
...
```

## PassiveRateGroup Alternative

**Note:** There's also `Svc::PassiveRateGroup` (passive component)
- No thread, no queue
- Synchronous execution on caller's thread
- Used when don't need rate group isolation or overrun detection
- Lighter weight

**How to apply:** When debugging rate group overruns:
1. Check `RgCycleSlips` telemetry
2. Check `RgMaxTime` to see execution time
3. Identify which rate group members are taking too long
4. Consider splitting into multiple rate groups or optimizing slow members
