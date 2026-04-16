---
name: F' Rate Group System Architecture
description: Periodic task scheduling using RateGroupDriver and ActiveRateGroup components
type: reference
---

# F' Rate Group System Architecture

The F' rate group system provides periodic scheduling for components. It divides a system tick into multiple rate groups operating at different frequencies.

## Rate Group Components

### Svc::RateGroupDriver (Svc/RateGroupDriver/docs/sdd.md)

**Purpose:** Take a single system tick and divide it into multiple rate groups

**Requirements:**
- RGD-001: Divide primary system tick into needed rate groups
- RCD-002: Be able to run in ISR context (interrupt-safe)

**Ports:**
- `CycleIn` (input, sync): Receive the system tick (Svc::Cycle)
- `CycleOut` (output): Drive rate groups (Svc::Cycle)

**Configuration:**
Call `configure(DividerSet& dividerSet)` with divider values for each output port.

**Example divider configuration:**

| SchedIn Rate | divider[0] | SchedOut[0] | divider[1] | SchedOut[1] | divider[2] | SchedOut[2] |
|--------------|------------|-------------|------------|-------------|------------|-------------|
| 1Hz          | 1          | 1Hz         | 2          | 0.5Hz       | 4          | 0.25Hz      |

**ISR compliance (can run in interrupt context):**
- No floating point calculations
- No mutexes
- No library calls with unknown side effects
- Fast implementation

**Why:** RateGroupDriver enables a single hardware timer to drive multiple rate groups without needing multiple timer sources. ISR-safe design allows direct connection to timer interrupts.

### Svc::ActiveRateGroup (Svc/ActiveRateGroup/docs/sdd.md)

**Purpose:** Active component that drives a set of components at a periodic rate

**Requirements:**
- ARG-001: Be woken up by async input port call
- ARG-002: Invoke output ports in order with context values from table
- ARG-003: Track execution time and report as telemetry
- ARG-004: Report warning event when cycle starts before previous completes (cycle slip)

**Ports:**
- `CycleIn` (input, async): Receive call to run one cycle (Svc::Cycle)
- `RateGroupMemberOut` (output): Rate group ports (Svc::Sched)

**Configuration:**
Call `configure(U32 contexts[], FwIndexType numContexts)` with context values for each output port.

**Key behaviors:**
- **Active component** with dedicated thread
- `CycleIn` port call enqueues message, waking the task
- Task calls each `RateGroupMemberOut` port in order, passing corresponding context value
- Tracks execution time from start to finish
- Detects **cycle slips**: if `CycleIn` called again before previous cycle completes
  - Sets flag at cycle start, checks flag at cycle end
  - Emits warning event and increments slip counter telemetry

**Context values:** Arbitrary U32 values passed to each rate group member. Components can use these to discriminate between multiple rate group calls.

**Why:** ActiveRateGroup decouples rate group execution from the calling thread (often ISR). The async input port and dedicated thread prevent long-running rate group members from blocking the timer interrupt.

### Svc::PassiveRateGroup (Svc/PassiveRateGroup/docs/sdd.md)

**Purpose:** Passive component that drives rate group members (no dedicated thread)

**Difference from ActiveRateGroup:**
- Passive component (no thread)
- Executes rate group members on caller's thread
- Suitable for low-priority rate groups or when thread budget is constrained

**When to use:**
- Low-frequency rate groups where dedicated thread isn't justified
- Systems with limited thread resources
- Rate groups that must execute synchronously with caller

## Rate Group Architecture

### Typical Topology

```
Hardware Timer (e.g., 100Hz)
    └─> RateGroupDriver
          ├─> CycleOut[0] (divider=1) → ActiveRateGroup (100Hz)
          │     ├─> RateGroupMemberOut[0] (context=0) → ComponentA
          │     ├─> RateGroupMemberOut[1] (context=1) → ComponentB
          │     └─> RateGroupMemberOut[2] (context=2) → ComponentC
          │
          ├─> CycleOut[1] (divider=10) → ActiveRateGroup (10Hz)
          │     ├─> RateGroupMemberOut[0] (context=0) → ComponentD
          │     └─> RateGroupMemberOut[1] (context=1) → ComponentE
          │
          └─> CycleOut[2] (divider=100) → ActiveRateGroup (1Hz)
                ├─> RateGroupMemberOut[0] (context=0) → ComponentF
                └─> RateGroupMemberOut[1] (context=1) → ComponentG
```

**Flow:**
1. Hardware timer triggers at base rate (e.g., 100Hz)
2. Timer ISR calls RateGroupDriver's `CycleIn` port
3. RateGroupDriver divides tick across multiple `CycleOut` ports based on dividers
4. Each ActiveRateGroup receives `CycleIn`, wakes task
5. ActiveRateGroup task calls all `RateGroupMemberOut` ports in sequence
6. Components receive `Svc::Sched` port call and execute periodic behavior

## Svc::Sched Port

**Purpose:** Port type used to invoke periodic behavior in components

**Arguments:**
- `context` (U32): Context value from rate group configuration

**Usage:**
```cpp
void MyComponent::schedIn_handler(NATIVE_INT_TYPE portNum, U32 context) {
    // Execute periodic behavior
    // context can discriminate between multiple rate group calls
}
```

## Rate Group Design Patterns

### Pattern 1: Single Rate Group Per Frequency
Most common pattern - one ActiveRateGroup per rate (e.g., 100Hz, 10Hz, 1Hz).

### Pattern 2: Priority-Based Rate Groups
Higher-priority components in faster rate groups; lower-priority in slower rate groups.

### Pattern 3: Context-Based Execution
Single component connected to multiple rate group ports; uses context value to determine which operation to execute.

### Pattern 4: Cycle Slip Detection
Monitor ActiveRateGroup telemetry for cycle slips:
- Indicates rate group execution time exceeds period
- May need to reduce rate group member workload or increase rate group period

## Rate Group Best Practices

**Thread priority:** ActiveRateGroup task priority should be:
- Higher than application tasks
- Lower than critical system tasks (e.g., communication drivers)
- Fast rate groups typically have higher priority than slow rate groups

**Execution time budget:** Each rate group member should complete quickly:
- Total execution time << rate group period
- Example: 10Hz rate group (100ms period) should complete in <80ms
- Leave margin for jitter and other system activity

**Cycle slip handling:**
- Monitor cycle slip telemetry
- Investigate and fix root cause (reduce workload, increase period, or optimize code)
- Do NOT ignore cycle slips - they indicate timing budget violation

**ISR safety:** If RateGroupDriver connected directly to ISR:
- Keep ISR short (just call CycleIn port)
- ActiveRateGroup async input port prevents blocking ISR
- Never use PassiveRateGroup with ISR input (would block interrupt)

**How to apply:**
- Start with 3-4 rate groups (e.g., 100Hz, 10Hz, 1Hz, 0.1Hz)
- Place control loops in fast rate groups (10-100Hz)
- Place telemetry/housekeeping in slow rate groups (1-10Hz)
- Place background tasks in very slow rate groups (0.1-1Hz)
- Configure hardware timer at highest needed rate, use RateGroupDriver for division
- Monitor cycle slip events during testing and operations
- Budget execution time carefully; measure actual execution time
