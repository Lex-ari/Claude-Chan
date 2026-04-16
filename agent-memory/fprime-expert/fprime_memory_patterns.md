---
name: F Prime Memory Management Patterns
description: Memory allocation during init, buffer pools at runtime, and flight software memory safety
type: reference
---

# F Prime Memory Management Patterns

F Prime provides two complementary memory management patterns for different phases and use cases.

## Flight Software Memory Constraints

**Standard:** Flight software coding standards typically forbid dynamic memory allocation during runtime.

**Why:**
- Safety: Heap fragmentation risks
- Reliability: Allocation failures unpredictable
- Determinism: Allocation time non-deterministic
- Verification: Harder to prove memory bounds

**F Prime approach:** Pre-allocate during initialization, reuse during runtime.

## Two Memory Patterns

| Pattern | Phase | Purpose | Key Components |
|---------|-------|---------|----------------|
| Memory Allocation | Initialization | Allocate memory blocks during setup for use during runtime | `Fw::MemAllocator`, `Fw::MallocAllocator` |
| Buffer Pool | Runtime | Allocate/deallocate buffers from pre-allocated pool | `Svc::BufferManager` |

## Memory Allocation Pattern (Initialization)

**When to use:**
- Memory requirements too large for stack
- Component needs internal memory of configurable size
- Multiple instances need different memory configurations
- Size determined at initialization, not compile-time

### Fw::MemAllocator Interface

**Purpose:** Abstraction layer over project-specified allocation mechanism

**Interface methods:**
```cpp
void* allocate(NATIVE_UINT_TYPE identifier, NATIVE_UINT_TYPE size);
void deallocate(NATIVE_UINT_TYPE identifier, void* ptr);
```

**Parameters:**
- `identifier`: Unique ID for this allocation (debugging/tracking)
- `size`: Bytes to allocate
- `ptr`: Pointer to deallocate

**Why abstraction:** Projects can provide custom allocators (static pools, specific allocators, etc.)

### Fw::MallocAllocator Implementation

**Standard implementation:** Delegates to `malloc()` / `free()`

**Usage:**
```cpp
Fw::MallocAllocator allocator;
void* memory = allocator.allocate(1, 1024);  // Allocate 1KB
// Use memory...
allocator.deallocate(1, memory);
```

**When safe:** During initialization only. Don't use malloc/free during runtime operations.

### Typical Workflow

**1. Component defines setup method:**
```cpp
class MyComponent : public MyComponentComponentBase {
public:
    void configure(Fw::MemAllocator& allocator, U32 bufferSize);
private:
    U8* m_buffer;
    U32 m_bufferSize;
};
```

**2. Topology calls configure during initialization:**
```cpp
void configureTopology() {
    Fw::MallocAllocator allocator;
    
    // Allocate memory during init
    myComp.configure(allocator, 10 * 1024);  // 10KB buffer
}
```

**3. Component allocates in configure:**
```cpp
void MyComponent::configure(Fw::MemAllocator& allocator, U32 bufferSize) {
    this->m_buffer = static_cast<U8*>(
        allocator.allocate(this->m_instanceId, bufferSize)
    );
    this->m_bufferSize = bufferSize;
}
```

**4. Component uses memory during runtime** (no more allocation)

**5. Topology deallocates during teardown:**
```cpp
void teardownTopology() {
    // Component deallocates in teardown method
    myComp.teardown(allocator);
}
```

### Example Use Cases

**Svc::BufferManager backing memory:**
```cpp
// BufferManager needs memory pool
bufferMgr.setup(
    allocator,          // Allocator for pool memory
    0,                  // Store ID
    numBins,            // Number of buffer sizes
    binSizes,           // Array of buffer sizes
    binCounts           // Array of buffer counts per size
);
```

**Svc::FrameAccumulator buffer:**
```cpp
// Accumulator needs buffer for frame assembly
frameAccum.configure(allocator, maxFrameSize);
```

**Component internal buffers:**
Any component needing large internal working memory.

### Fw::MemAllocatorRegistry (Optional)

**Purpose:** Manage multiple allocator types in one system

**Use case:** Different allocators for different memory regions (e.g., fast RAM, slow RAM)

**Pattern:**
```cpp
Fw::MemAllocatorRegistry registry;
Fw::MallocAllocator fastAllocator;
Fw::MallocAllocator slowAllocator;

registry.registerAllocator("fast", fastAllocator);
registry.registerAllocator("slow", slowAllocator);

Fw::MemAllocator* alloc = registry.getAllocator("fast");
```

## Buffer Pool Pattern (Runtime)

**When to use:**
- Components need temporary working memory during operation
- Buffer sizes vary based on runtime conditions
- Memory must be shared efficiently across system
- Want safe runtime "allocation" without violating flight software standards

### Svc::BufferManager Component

**Purpose:** Pre-allocated buffer pool, runtime allocation/deallocation via ports

**Key features:**
- Pools allocated at initialization (using Memory Allocation pattern)
- Runtime allocation via port calls
- Multiple buffer sizes (bins) supported
- Allocation failure detectable (empty pool)
- Ownership tracking (which component has which buffer)

### Configuration at Initialization

**Setup method:**
```cpp
bufferMgr.setup(
    allocator,              // Fw::MemAllocator for backing memory
    storeId,                // Store identifier
    numBins,                // Number of buffer size bins
    binSizes,               // U32 array: size of each bin
    binCounts               // U32 array: count of buffers per bin
);
```

**Example:**
```cpp
Fw::MallocAllocator allocator;
U32 binSizes[] = {128, 512, 2048};      // 3 bins: 128B, 512B, 2KB
U32 binCounts[] = {10, 5, 2};           // 10x128B, 5x512B, 2x2KB

bufferMgr.setup(allocator, 0, 3, binSizes, binCounts);
```

**Memory allocated:** Total = (128×10) + (512×5) + (2048×2) = 1280 + 2560 + 4096 = 7936 bytes

### Runtime Buffer Allocation

**Component requests buffer via port:**
```cpp
// Request 500-byte buffer
Fw::Buffer buffer;
this->allocate_out(0, 500, buffer);

// Check if allocation succeeded
if (buffer.isValid()) {
    // Use buffer
    U8* data = buffer.getData();
    U32 size = buffer.getSize();
    
    // Fill buffer with data
    memcpy(data, myData, dataSize);
    
    // Pass to another component or deallocate
} else {
    // Allocation failed - no buffers available
    this->log_WARNING_HI_BufferAllocationFailed();
}
```

**BufferManager behavior:**
- Finds smallest bin that fits requested size
- Returns buffer from that bin
- If bin empty, allocation fails (buffer.isValid() == false)

### Runtime Buffer Deallocation

**Return buffer to pool via port:**
```cpp
// Return buffer to BufferManager
this->deallocate_out(0, buffer);
```

**Critical:** Must return buffers to avoid pool exhaustion.

### Buffer Ownership and Passing

**Pattern:** Buffers can be passed between components via ports

**Example flow:**
```cpp
// Component A allocates
this->allocate_out(0, size, buffer);

// Component A fills and sends to Component B
this->dataOut_out(0, buffer);

// Component B receives and uses
void dataIn_handler(const Fw::Buffer& buffer) {
    U8* data = buffer.getData();
    // Process data...
    
    // Component B returns to BufferManager
    this->deallocate_out(0, buffer);
}
```

**Ownership transfer:** Passing buffer transfers responsibility for deallocation.

### Buffer Pool Exhaustion

**What happens:** If all buffers allocated, new requests fail

**Detection:**
```cpp
this->allocate_out(0, size, buffer);
if (!buffer.isValid()) {
    // Pool exhausted - handle gracefully
    // Options: Drop data, event, try again later
}
```

**Prevention:**
- Size pools appropriately for expected concurrency
- Ensure components deallocate promptly
- Monitor BufferManager telemetry (free buffer counts)

### Common Use Cases

**Communication packets:**
```cpp
// Allocate buffer for incoming packet
this->allocate_out(0, packetSize, buffer);
// Receive into buffer
// Pass to decoder
// Decoder deallocates when done
```

**File transfer:**
```cpp
// Allocate buffer for file chunk
this->allocate_out(0, chunkSize, buffer);
// Read file data into buffer
// Send to downlink
// Downlink deallocates after transmission
```

**Framing/Deframing:**
```cpp
// Allocate buffer for frame assembly
this->allocate_out(0, maxFrameSize, buffer);
// Accumulate data into frame
// Send completed frame
// Deallocate after processing
```

## Combining Both Patterns

**Common pattern:** Use Memory Allocation to set up BufferManager, then use Buffer Pool at runtime.

```cpp
// During initialization (Memory Allocation pattern)
void configureTopology() {
    Fw::MallocAllocator allocator;
    U32 binSizes[] = {128, 512, 2048};
    U32 binCounts[] = {10, 5, 2};
    
    // BufferManager uses Memory Allocation for pool
    bufferMgr.setup(allocator, 0, 3, binSizes, binCounts);
}

// During runtime (Buffer Pool pattern)
void MyComponent::processData() {
    Fw::Buffer buffer;
    this->allocate_out(0, 500, buffer);  // Runtime buffer request
    
    if (buffer.isValid()) {
        // Use buffer...
        this->deallocate_out(0, buffer);  // Runtime buffer return
    }
}
```

## Memory Safety Guidelines

1. **No runtime malloc/free:** Use patterns above, not direct malloc/free in handlers
2. **Pre-allocate during init:** Determine memory needs, allocate during setup
3. **Check allocation success:** Always check buffer.isValid() after allocation
4. **Deallocate promptly:** Don't hold buffers longer than needed
5. **Size pools appropriately:** Based on max concurrency, not just typical case
6. **Monitor pool health:** Use BufferManager telemetry to detect exhaustion
7. **Handle allocation failure:** Have graceful degradation strategy
8. **Document ownership:** Clear who responsible for deallocation
9. **Test exhaustion cases:** Unit test buffer pool exhaustion scenarios
10. **Static analysis:** Use tools to verify no dynamic allocation in runtime paths

## How to apply

1. **Initialization phase:** Use Fw::MemAllocator for component setup (large buffers, configurable sizes)
2. **Runtime phase:** Use Svc::BufferManager for temporary buffers (packets, transfers, processing)
3. **BufferManager setup:** Leverage Fw::MemAllocator to provide BufferManager's backing memory
4. **Component design:** Components should request/return buffers, not manage pools themselves
5. **Pool sizing:** Calculate worst-case concurrent buffer needs, add margin
6. **Check validity:** Always check buffer.isValid() before use
7. **Clear ownership:** Document which component responsible for deallocation
8. **Teardown:** Deallocate initialization memory during teardown (if applicable)
9. **Testing:** Test buffer exhaustion paths in unit tests
10. **Telemetry:** Monitor BufferManager free buffer counts in operations
