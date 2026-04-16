---
name: F' Telemetry System Architecture
description: Telemetry channel management including TlmChan component and Fw::Tlm port
type: reference
---

# F' Telemetry System Architecture

The F' telemetry system enables flight software to report component state and measurement data to the ground system.

## Telemetry Port Type

### Fw::Tlm Port (Fw/Tlm/docs/sdd.md)

**Purpose:** Pass a serialized telemetry value with channel ID and timestamp

**Arguments:**
- `id` (FwChanIdType): Telemetry channel ID
- `timeTag` (Fw::Time): Time when channel was written
- `tlmBuffer` (Fw::TlmBuffer): Serialized channel value

### Fw::TlmBuffer Serializable

The `Fw::TlmBuffer` class contains a buffer holding the serialized value of a telemetry channel. This allows the framework to store and transport channels without knowing their types.

### Fw::TlmPacket

The `Fw::TlmPacket` class (derived from `Fw::ComPacket`) provides methods for encoding telemetry packets containing multiple channel updates.

**To fill a packet with telemetry:**
1. Instantiate a `TlmPacket`
2. Call `resetPktSer()` to start adding values
3. Call `addValue()` repeatedly until buffer is full or all values added
   - Returns `Fw::FW_SERIALIZE_NO_ROOM_LEFT` when buffer is full
4. Extract the `ComBuffer` with `getBuffer()` and send to ground system
5. Repeat for additional channels

**Packet layout:**
```
| Telemetry Packet Descriptor | Chan 1 ID | Chan 1 timestamp | Chan 1 Value | ... | Chan N ID | Chan N timestamp | Chan N Value | Leftover buffer space |
```

**To extract telemetry from a packet:**
1. Instantiate a `TlmPacket`
2. Pass serialized buffer via `setBuffer()`
3. Call `resetPktDeser()` to verify packet descriptor and start extraction
4. Call `extractValue()` for each entry (user must know value size)
   - Returns `Fw::FW_DESERIALIZE_BUFFER_EMPTY` when no more data
5. Repeat for additional packets

## Svc::TlmChan Component (Svc/TlmChan/docs/sdd.md)

**Purpose:** Store telemetry values written by components; periodically push updated values for downlink

**Requirements:**
- TLC-001: Provide interface to submit telemetry
- TLC-002: Provide interface to read telemetry
- TLC-003: Provide interface to run periodically to write telemetry
- TLC-004: Write changed telemetry channels when invoked by run port

**Ports:**
- `TlmRecv` (input, sync): Update a telemetry channel (called by components)
- `TlmGet` (input, sync): Read a telemetry channel (called by requestors)
- `Run` (input, async): Execute cycle to write changed telemetry channels
- `PktSend` (output): Write packets with updated telemetry (Fw::Com)

**Key behaviors:**
- Stores channel values in **double-buffered table** (allows read while writing)
- Uses **hash table** for fast channel lookup (configurable in `TlmChanImplCfg.hpp`)
- Tracks which channels have changed since last periodic push
- On `Run` port call: Packages all changed channels into packets and sends via `PktSend`
- Clears "changed" flags after successful send

**Hash table configuration:**
- `TLMCHAN_NUM_TLM_HASH_SLOTS`: Number of hash buckets (must be ≥ number of channels)
- `TLMCHAN_HASH_MOD_VALUE`: Hash modulo value for distribution
- See `TlmChanImplCfg.h` for tuning procedure
- Determine channel count with: `make comp_report_gen` from deployment directory

**Nonexistent channel behavior:**
- If `TlmGet` requests a channel that was never written, returns empty buffer
- No way to distinguish "not yet written" from "doesn't exist" programmatically

**Why:** TlmChan centralizes telemetry storage and provides efficient periodic downlink. Double buffering prevents read contention. Hash table enables O(1) lookup even with hundreds of channels.

## Telemetry Flow Architecture

```
Component A                  Component B
     |                            |
     └─ tlm_out ──┐          ┌───┘
                  ↓          ↓
               Svc::TlmChan (stores all channels)
                      |
                      | Run port (periodic, e.g., 1Hz)
                      ↓
              Package changed channels
                      |
                      └─ PktSend → TlmPacketizer → Downlink
```

**Key insight:** Components write telemetry individually whenever values change. TlmChan aggregates changes and sends periodic packets to downlink, preventing channel update rate from overwhelming the link.

## Telemetry Definition Pattern

In component FPP:
```
telemetry MY_STATE: U32 \
    update on change \
    format "{} state value"
```

In component C++:
```cpp
// Write telemetry channel
this->tlmWrite_MY_STATE(stateValue);
```

**Auto-generated code handles:**
- Serialization of value into Fw::TlmBuffer
- Calling tlm_out port with channel ID, timestamp, and buffer
- Obtaining timestamp from time_out port

## Telemetry Update Strategies

### Update on Change
Default behavior - channel written whenever value changes.

**When to use:** Most telemetry

### Update Always
Channel written every time `tlmWrite_X()` called, even if value unchanged.

**When to use:** Rarely; when ground system needs confirmation of updates

### Update Periodic
Channel written on periodic schedule regardless of changes (not standard F').

**When to use:** Some missions implement this via custom rate group patterns

## Telemetry vs. Parameters

**Telemetry:** Component → Ground (state/measurements)
**Parameters:** Ground → Component (configuration values)

Don't confuse the two! They use different port types and different components (TlmChan vs. PrmDb).

**How to apply:**
- Use telemetry for reporting component state, sensor values, counters
- Keep telemetry channels simple types (primitives, small structs)
- Avoid high-rate telemetry that could saturate downlink
- TlmChan Run port rate determines downlink packet rate (typically 1-10Hz)
- Use "update on change" for most channels to minimize bandwidth
- Consider telemetry filtering for very high-rate channels
