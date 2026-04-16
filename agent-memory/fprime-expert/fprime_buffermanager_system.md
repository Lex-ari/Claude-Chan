---
name: F Prime BufferManager Pool Management System
description: BufferManager bin configuration, allocation strategy, buffer lifecycle, and pool sizing
type: reference
---

# Svc::BufferManager Pool Management System

## Location
- SDD: `fprime/Svc/BufferManager/docs/sdd.md`
- User Guide: `fprime/docs/user-manual/framework/memory-management/buffer-pool.md`

## Purpose
Provides fixed-size buffer pool management for inter-component communication. Allocates buffers on request, tracks ownership, and deallocates on return.

## Component Type
**Passive component** - No thread, handlers execute on caller's thread

## Key Ports

### Input Ports
- `bufferGetCallee: Fw.BufferGet (guarded input)` - Allocate buffer request
- `bufferSendIn: Fw.BufferSend (guarded input)` - Deallocate buffer
- `schedIn: Svc.Sched (sync input, optional)` - Write telemetry

**Port Type:** Guarded = mutex protected, synchronous

## Buffer Bin Configuration

### BufferBin Structure
```cpp
struct BufferBin {
    U32 bufferSize;   // Size of each buffer in this bin (bytes)
    U32 numBuffers;   // Number of buffers in this bin
};
```

### BufferBins Structure
```cpp
struct BufferBins {
    BufferBin bins[BUFFERMGR_MAX_NUM_BINS];  // Array of bin configurations
};
```

**Configuration Constant:** `BUFFERMGR_MAX_NUM_BINS` (default 10)

**Location:** `config/BufferManagerComponentImplCfg.hpp`

### Setup Method
```cpp
void setup(
    U16 mgrID,                     // Unique manager ID
    U16 memID,                     // Memory allocator ID
    Fw::MemAllocator& allocator,   // Memory allocator instance
    const BufferBins& bins         // Bin configuration
);
```

**Example Configuration:**
```cpp
Svc::BufferManager::BufferBins bins;
memset(&bins, 0, sizeof(bins));

bins.bins[0].bufferSize = 256;    // Small buffers
bins.bins[0].numBuffers = 10;

bins.bins[1].bufferSize = 1024;   // Medium buffers
bins.bins[1].numBuffers = 5;

bins.bins[2].bufferSize = 4096;   // Large buffers
bins.bins[2].numBuffers = 2;

bufferManager.setup(1, 0, allocator, bins);
```

## Internal State

### AllocatedBuffer Structure
```cpp
struct AllocatedBuffer {
    bool allocated;        // Buffer is currently allocated
    U32 size;              // Buffer size
    U8* data;              // Pointer to buffer memory
    FwIndexType bin;       // Which bin this belongs to
    FwIndexType id;        // Buffer ID within bin
};
```

**Storage:** Array of all buffers across all bins

## Allocation Strategy

**Handler:** `bufferGetCallee_handler(portNum, size)`

**Algorithm:**

1. **Search for smallest sufficient buffer:**
   - Start with smallest bin
   - Find first unallocated buffer with `size >= requested size`

2. **Mark buffer as allocated:**
   ```cpp
   buffer->allocated = true;
   ```

3. **Create Fw::Buffer instance:**
   ```cpp
   Fw::Buffer buffer(
       managerID,   // Manager ID (for validation on return)
       bufferID,    // Buffer ID (for validation on return)
       data,        // Pointer to buffer memory
       size         // Actual buffer size
   );
   ```

4. **Return buffer to caller**

5. **If no buffer available:**
   - Return empty buffer (size = 0)
   - Caller must handle allocation failure

**Key Design:** First-fit allocation with size-based bin selection

## Deallocation Flow

**Handler:** `bufferSendIn_handler(portNum, buffer)`

**Algorithm:**

1. **Check if empty buffer:**
   ```cpp
   if (buffer.getSize() == 0) {
       log_WARNING_LO_EmptyBufferReturned();
       return;
   }
   ```

2. **Extract context from buffer:**
   ```cpp
   U32 context = buffer.getContext();
   U16 managerID = extractManagerID(context);
   U16 bufferID = extractBufferID(context);
   ```

3. **Validate manager ID:**
   ```cpp
   FW_ASSERT(managerID == m_mgrID);
   ```

4. **Validate buffer ID:**
   ```cpp
   FW_ASSERT(bufferID < m_totalBuffers);
   ```

5. **Find allocated buffer:**
   ```cpp
   AllocatedBuffer* allocBuf = &m_buffers[bufferID];
   ```

6. **Validate buffer state:**
   ```cpp
   FW_ASSERT(allocBuf->allocated == true);
   FW_ASSERT(allocBuf->data == buffer.getData());
   FW_ASSERT(allocBuf->size >= buffer.getSize());
   ```

7. **Mark as deallocated:**
   ```cpp
   allocBuf->allocated = false;
   ```

## Buffer Lifecycle

### Typical Flow:

1. **Allocation:**
   ```cpp
   Fw::Buffer buf = bufferManager.bufferGetCallee(requestedSize);
   if (buf.getSize() == 0) {
       // Allocation failed, no buffers available
   }
   ```

2. **Usage:**
   ```cpp
   // Sending component fills buffer
   memcpy(buf.getData(), data, dataSize);
   buf.setSize(actualSize);  // Can be <= allocated size
   ```

3. **Transfer:**
   ```cpp
   // Send to receiving component
   receivingComponent.bufferSendIn(buf);
   ```

4. **Deallocation:**
   ```cpp
   // Receiving component (after use):
   bufferManager.bufferSendIn(buf);
   ```

## Buffer Context Encoding

**Purpose:** Embed manager ID and buffer ID in buffer context field

**Encoding:**
```
Context = (managerID << 16) | bufferID
```

**Decoding:**
```cpp
U16 managerID = (context >> 16) & 0xFFFF;
U16 bufferID = context & 0xFFFF;
```

**Why:** Validates correct buffer returned to correct manager

## Telemetry (Optional)

**Handler:** `schedIn_handler(portNum, context)`

**Telemetry Channels:**
- Statistics about buffer allocation
- High water marks
- Allocation failures

**Note:** Telemetry ports optional; BufferManager functions without them

## Memory Allocation

**Allocator:** Provided via `Fw::MemAllocator` interface

**Example Allocators:**
- `Fw::MallocAllocator` - Uses heap (malloc/free)
- Custom allocators - Static pools, special memory regions

**Allocation Timing:** All buffers allocated during `setup()` call

**Deallocation:** Via `deallocateBuffer()` method (call before destructor)

## Error Handling and Assertions

### Assertions (Fatal)
- Wrong manager ID returned
- Invalid buffer ID returned
- Buffer not marked as allocated (double free)
- Buffer size larger than originally allocated
- Buffer pointer doesn't match original

### Warnings (Non-Fatal)
- Empty buffer returned (size = 0)

### Graceful Degradation
- Return empty buffer if none available (no assertion)

## Critical Design Patterns

### 1. Fixed-Size Pool
- All buffers allocated at initialization
- No dynamic allocation during runtime
- Predictable memory usage
- Deterministic performance

### 2. Multiple Bin Sizes
- Reduces memory waste
- Small buffers for small messages
- Large buffers for large messages
- Fallback to larger bin if smaller exhausted

### 3. First-Fit Allocation
- Finds smallest sufficient buffer
- Minimizes fragmentation
- Simple and fast (O(N) search)

### 4. Context-Based Validation
- Manager ID prevents cross-manager returns
- Buffer ID enables lookup
- Detects corruption and misuse

### 5. Passive Component Design
- No thread overhead
- Synchronous operation
- Minimal latency
- Guarded ports provide thread safety

### 6. Empty Buffer Signaling
- Size = 0 indicates allocation failure
- Caller decides how to handle
- No exceptions or error returns

### 7. Order-Independent Deallocation
- Buffers can be returned in any order
- No lifetime restrictions
- Simplifies component design

## Bin Sizing Strategy

**Guidelines:**

1. **Count Messages:**
   - Identify all inter-component buffer transfers
   - Determine size of each message type
   - Count maximum concurrent messages

2. **Group by Size:**
   - Group messages into size ranges
   - Create bin for each size range
   - Add overhead for headers/metadata

3. **Add Margin:**
   - Add 20-50% extra buffers for margin
   - Account for bursts and transients

4. **Monitor Usage:**
   - Use telemetry to track high water marks
   - Adjust bin sizes if allocation failures occur

**Example Analysis:**
```
Message Type           Size    Count   Bin
--------------------------------------------
Telemetry packets      256     10      Small (256, 15 buffers)
File chunks            1024    5       Medium (1024, 8 buffers)
Image frames           4096    2       Large (4096, 3 buffers)
```

## Common Usage Pattern

### Sender Component:
```cpp
// Request buffer
Fw::Buffer buf = bufferGet_out(0, dataSize);

if (buf.getSize() > 0) {
    // Fill buffer
    memcpy(buf.getData(), myData, dataSize);
    buf.setSize(dataSize);

    // Send to receiver
    bufferSend_out(0, buf);
} else {
    // Handle allocation failure
    log_WARNING_NO_BUFFERS();
}
```

### Receiver Component:
```cpp
void bufferRecv_handler(FwIndexType portNum, Fw::Buffer& buf) {
    // Use buffer data
    processData(buf.getData(), buf.getSize());

    // Return buffer to manager
    bufferSend_out(0, buf);
}
```

### Topology Integration:
```cpp
// Setup buffer manager
bufferManager.setup(1, 0, allocator, bins);

// Connections
sender.bufferGet → bufferManager.bufferGetCallee
sender.bufferSend → receiver.bufferRecv
receiver.bufferSend → bufferManager.bufferSendIn
```

## BufferManager vs Dynamic Allocation

**BufferManager Advantages:**
- Deterministic timing (no malloc delays)
- No fragmentation
- Bounded memory usage
- Detects buffer leaks (all allocated at init)

**Dynamic Allocation Advantages:**
- Flexible sizing
- No pre-allocation overhead
- Simpler configuration

**When to Use BufferManager:**
- Flight software (need determinism)
- Real-time systems
- Memory-constrained systems
- High-reliability applications

**How to apply:** When setting up buffer pools:
1. Analyze message flows in topology
2. Size bins based on actual message sizes
3. Add margin for burst scenarios
4. Monitor telemetry for allocation failures
5. Adjust bin configuration if needed
6. Validate manager ID is unique across all buffer managers in system
