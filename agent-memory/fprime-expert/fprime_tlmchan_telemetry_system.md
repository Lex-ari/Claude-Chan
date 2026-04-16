---
name: F Prime TlmChan Telemetry Storage System
description: TlmChan double-buffering, hash table implementation, and telemetry flow
type: reference
---

# Svc::TlmChan Telemetry Storage System

## Location
- SDD: `fprime/Svc/TlmChan/docs/sdd.md`
- FPP: `fprime/Svc/TlmChan/TlmChan.fpp`
- Implementation: `fprime/Svc/TlmChan/TlmChan.hpp/cpp`

## Purpose
Stores telemetry channel values in serialized form, provides read interface, and periodically sends updated channels for downlink.

## Component Type
**Active component** - Has own thread and message queue

## Key Ports

### Input Ports
- `TlmRecv: Fw.Tlm (guarded input)` - Receives telemetry updates from components
- `TlmGet: Fw.TlmGet (guarded input)` - Returns telemetry value by ID
- `Run: Svc.Sched (async input)` - Triggers packet send cycle

### Output Ports
- `PktSend: Fw.Com` - Sends telemetry packets for downlink

## Internal Data Structures

### TlmEntry Structure
```cpp
struct tlmEntry {
    FwChanIdType id;          // Telemetry channel ID
    bool updated;             // Has been written since last packet send
    Fw::Time lastUpdate;      // Time of last update
    Fw::TlmBuffer buffer;     // Serialized telemetry value
    tlmEntry* next;           // Next bucket in hash chain
    bool used;                // Entry has been allocated
    FwChanIdType bucketNo;    // Bucket number (for testing)
};
```

### TlmSet Structure (Double Buffer)
```cpp
struct TlmSet {
    TlmEntry* slots[TLMCHAN_NUM_TLM_HASH_SLOTS];  // Hash table slots
    TlmEntry buckets[TLMCHAN_HASH_BUCKETS];       // Bucket storage
    FwChanIdType free;                            // Next free bucket
} m_tlmEntries[2];  // Two sets for double buffering
```

### Active Buffer
```cpp
U32 m_activeBuffer;  // Which buffer (0 or 1) is active
```

## Hash Algorithm

**Function:** `doHash(FwChanIdType id)`

**Algorithm:**
```cpp
return (id % TLMCHAN_HASH_MOD_VALUE) % TLMCHAN_NUM_TLM_HASH_SLOTS;
```

**Purpose:** Map channel ID to hash slot

**Collision Handling:** Chaining via `next` pointers

**Configuration:** `config/TlmChanImplCfg.h`
- `TLMCHAN_NUM_TLM_HASH_SLOTS` - Number of hash table slots
- `TLMCHAN_HASH_BUCKETS` - Total buckets available (>= number of channels)
- `TLMCHAN_HASH_MOD_VALUE` - Modulus for hash distribution

**Tuning:** Adjust to balance memory vs hash distribution

## Double-Buffering Architecture

**Purpose:** Allow telemetry writes while reading for downlink without blocking

**Mechanism:**
1. **Active buffer** receives telemetry updates
2. On `Run` port call:
   - Lock mutex
   - Swap active buffer: `m_activeBuffer = 1 - m_activeBuffer`
   - Clear `updated` flags in new active buffer
   - Unlock mutex
3. Read from **inactive buffer** to create packets (no lock needed)
4. This allows updates to continue in active buffer while reading inactive

**Benefits:**
- Minimal lock contention
- Updates never blocked by packet generation
- Consistent snapshot of telemetry at packet send time

## Telemetry Write Flow

**Handler:** `TlmRecv_handler(portNum, id, timeTag, val)`

**Port Type:** Guarded input (mutex protected)

**Algorithm:**

1. **Compute hash index:**
   ```cpp
   FwChanIdType index = doHash(id);
   ```

2. **Search for existing entry or add new:**
   - If slot is empty:
     - Allocate bucket from free list
     - Set as head of slot
   - If slot has entries:
     - Walk chain looking for matching `id`
     - If found: use existing entry
     - If not found: allocate new bucket, add to end of chain

3. **Store telemetry:**
   ```cpp
   entryToUse->used = true;
   entryToUse->id = id;
   entryToUse->updated = true;
   entryToUse->lastUpdate = timeTag;
   entryToUse->buffer = val;
   ```

4. **Assertions:**
   - Assert if run out of buckets (`free >= TLMCHAN_HASH_BUCKETS`)

**Thread Safety:** Guarded port provides mutex protection

## Telemetry Read Flow

**Handler:** `TlmGet_handler(portNum, id, timeTag, val)`

**Port Type:** Guarded input (mutex protected)

**Algorithm:**

1. **Compute hash index:**
   ```cpp
   FwChanIdType index = doHash(id);
   ```

2. **Search in BOTH buffers:**
   - Search active buffer for entry with matching `id`
   - Search inactive buffer for entry with matching `id`

3. **Determine which entry to return:**
   - If found in both buffers:
     - Compare time tags using `Fw::Time::compare()`
     - Return entry with more recent time tag
     - If incomparable, return the one that's `updated`
   - If found in only one buffer:
     - Return that entry
   - If not found in either:
     - Return empty buffer (`val.resetSer()`)
     - Return `Fw::TlmValid::INVALID`

**Why Search Both:** Active buffer might have more recent update than inactive

**Return Value:** `Fw::TlmValid::VALID` or `INVALID`

## Packet Send Flow (Run Handler)

**Handler:** `Run_handler(portNum, context)`

**Triggered by:** Rate group calling `Run` port

**Algorithm:**

1. **Swap active buffer:**
   ```cpp
   lock();
   m_activeBuffer = 1 - m_activeBuffer;
   // Clear updated flags in new active buffer
   for (entry = 0; entry < TLMCHAN_HASH_BUCKETS; entry++) {
       m_tlmEntries[m_activeBuffer].buckets[entry].updated = false;
   }
   unLock();
   ```

2. **Create packet from inactive buffer:**
   ```cpp
   Fw::TlmPacket pkt;
   pkt.resetPktSer();
   ```

3. **Iterate through all buckets in inactive buffer:**
   ```cpp
   for (entry = 0; entry < TLMCHAN_HASH_BUCKETS; entry++) {
       TlmEntry* p_entry = &m_tlmEntries[1 - m_activeBuffer].buckets[entry];
       if (p_entry->updated && p_entry->used) {
           // Add to packet
       }
   }
   ```

4. **Add entries to packet:**
   ```cpp
   stat = pkt.addValue(p_entry->id, p_entry->lastUpdate, p_entry->buffer);
   ```

5. **Handle packet full:**
   - If `FW_SERIALIZE_NO_ROOM_LEFT`:
     - Send current packet
     - Reset packet
     - Add entry to new packet
   - If `FW_SERIALIZE_OK`:
     - Continue adding entries
   - Other status → assert (shouldn't happen)

6. **Clear updated flag:**
   ```cpp
   p_entry->updated = false;
   ```

7. **Send remnant packet:**
   ```cpp
   if (pkt.getNumEntries() > 0) {
       PktSend_out(0, pkt.getBuffer(), 0);
   }
   ```

## Critical Design Patterns

### 1. Double-Buffering for Concurrency
- Allows reads and writes without blocking
- Writer always writes to active buffer (with lock)
- Reader reads from inactive buffer (without lock)
- Swap is atomic and quick (just change active index)

### 2. Hash Table with Chaining
- O(1) average case lookup
- Handles collisions via linked list chains
- Fixed memory allocation (no dynamic allocation after init)

### 3. Update-Only Packet Generation
- Only sends channels that have `updated = true`
- Minimizes downlink bandwidth
- Component can write all channels, but only changed ones downlinked

### 4. Serialized Storage
- Stores telemetry in serialized form (`Fw::TlmBuffer`)
- Type-agnostic storage
- Components serialize, TlmChan just stores bytes

### 5. Time Tag Comparison
- Uses `Fw::Time::compare()` for time tag ordering
- Handles incomparable times (different time bases)
- Always returns most recent value

### 6. Guarded Ports for Thread Safety
- Both `TlmRecv` and `TlmGet` are guarded
- Mutex protects hash table access
- Lock held for short duration (just hash lookup + update)

## Configuration and Tuning

**File:** `config/TlmChanImplCfg.h`

**Key Parameters:**
- `TLMCHAN_NUM_TLM_HASH_SLOTS` - Number of hash slots
- `TLMCHAN_HASH_BUCKETS` - Total buckets (must be >= number of channels in system)
- `TLMCHAN_HASH_MOD_VALUE` - Hash distribution factor

**Tuning Procedure:** See `TlmChanImplCfg.h` for instructions on balancing memory vs performance

**Determining Channel Count:**
```bash
make comp_report_gen  # From deployment directory
```

## Integration with Component Telemetry

**Component Side:**
1. Component defines telemetry channel in FPP
2. Autocoder generates `tlmWrite_<ChannelName>()` method
3. Method serializes value into `Fw::TlmBuffer`
4. Calls `Tlm_out()` port with channel ID, time, and buffer
5. Connected to `TlmChan.TlmRecv` port

**TlmChan Side:**
1. Receives on `TlmRecv` handler
2. Stores in hash table
3. Periodically sends on `PktSend` when `Run` called

**How to apply:** When debugging missing telemetry:
1. Check if channel is being written by component
2. Check if TlmChan `Run` port is being called periodically
3. Check if `PktSend` port is connected to downlink path
4. Verify hash table has enough buckets for all channels
