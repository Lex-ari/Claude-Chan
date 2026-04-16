---
name: F' File Management Architecture
description: File uplink, downlink, and management components including packet-based transfer
type: reference
---

# F' File Management Architecture

F' provides comprehensive file management for uplink, downlink, and on-board file operations.

## File Packet Format

All file transfers use **Fw::FilePacket** (Fw/FilePacket/docs/sdd.md) as the common packet format.

### Packet Types

1. **START packet:** Begin file transfer, provides metadata
2. **DATA packet:** Contains file data chunk
3. **END packet:** Complete file transfer, includes checksum
4. **CANCEL packet:** Cancel in-progress transfer

### Sequence Index
Each packet has a sequence index (incremental counter) to detect:
- Missing packets
- Out-of-order packets
- Duplicate packets

## Svc::FileUplink Component (Svc/FileUplink/docs/sdd.md)

**Purpose:** Receive file packets, assemble into files, store in non-volatile storage

**Requirements:**
- FPRIME-FU-001: Receive file packets, assemble them, store in on-board storage
- FPRIME-FU-002: Announce completion of uplinked files

**Ports:**
- `bufferSendIn` (input, async): Receives buffers containing file packets
- `bufferSendOut` (output): Returns buffers for deallocation
- `pingIn`/`pingOut`: Health check ports
- `fileAnnounce` (output): Announces receipt of uplinked file (Svc::FileAnnounce)

**State machine:**

| State | Description | Next State Trigger |
|-------|-------------|-------------------|
| START | Awaiting START packet | START packet → DATA |
| DATA | Receiving DATA packets | END packet → START |

**Receive mode:** Tracks expected next packet type (START or DATA).

**Key behaviors:**
- START packet: Opens file for writing
- DATA packet: Writes data at specified offset
- END packet: Verifies checksum (CCSDS CFDP method), closes file, announces completion
- CANCEL packet: Closes file, emits cancel event, returns to START mode
- Out-of-order packet: Emits warning, may abort transfer
- Packet out-of-bounds: Emits warning (offset/size invalid for file)

**Checksum method:** Uses CCSDS File Delivery Protocol (CFDP) checksum algorithm (§4.1.2 of CFDP Recommended Standard).

**Why active component?** File I/O operations are slow and blocking. Active component prevents blocking the communication receive path.

## Svc::FileDownlink Component (Svc/FileDownlink/docs/sdd.md)

**Purpose:** Read files from non-volatile storage, partition into packets, send to ground

**Requirements:**
- FD-001: Queue list of files to downlink
- FD-002: Read file, partition into packets, send packets
- FD-003: Wait for cooldown after completing file before starting next
- FD-004: Issue warning if file with zero size encountered

**Ports:**
- `sendFile` (input, guarded): Enqueue file for downlink (Svc::SendFileRequest)
- `fileComplete` (output): Emit notifications when file downlink completes (Svc::SendFileComplete)
- `Run` (input, async): Periodic clock for state machine
- `bufferGet` (output): Request buffers for file packets
- `bufferSendOut` (output): Send buffers containing file packets

**Commands:**
- **SendFile:** Enqueue file for downlink (source file, dest file name)
- **SendPartial:** Enqueue partial file (source, dest, offset, length)
  - length=0 means read to end of file
- **Cancel:** Cancel current file downlink

**Constants (set at instantiation):**
- `downlinkPacketSize`: Packet size for downlink
- `cooldown`: Cooldown time (ms) after file completes before starting next
- `cycle time`: Frequency (ms) of Run port calls
- `file queue depth`: Max number of files in downlink queue

**State machine:**

| State | Description |
|-------|-------------|
| IDLE | No file downlink in progress |
| DOWNLINK | Performing file downlink |
| CANCEL | Canceling file downlink |
| WAIT | Waiting for buffer to be returned |
| COOLDOWN | Waiting before starting next file |

**File queue:** Multiple files can be enqueued via `sendFile` port or **SendFile** command. FileDownlink processes them sequentially.

**Cooldown purpose:** Prevents continuous file downlink from saturating communication link. Allows backlog to clear between files.

**Why cooldown?** File downlink can generate high data rates. Cooldown prevents overwhelming downlink capacity, allows telemetry and commands to be processed.

**Maximum file size:** Limited to 4GiB. Larger files result in bad size error.

## Svc::FileManager Component (Svc/FileManager/docs/sdd.md)

**Purpose:** Provide commands for on-board file operations

**Common commands:**
- **CreateDirectory:** Create directory
- **RemoveDirectory:** Remove empty directory
- **RemoveFile:** Delete file
- **MoveFile:** Move/rename file
- **ShellCommand:** Execute shell command (if enabled)
- **FileSize:** Report file size
- **ListDirectory:** List directory contents

**Why separate component?** Centralizes file operations, provides common interface, enforces permissions and validation.

## File Transfer Architecture

### Uplink Flow
```
Ground System
  └─> File packet stream (START, DATA*, END)
      └─> ByteStreamDriver (e.g., TCP)
          └─> Deframer
              └─> FileUplink (bufferSendIn)
                  ├─> Assemble packets into file
                  ├─> Verify checksum
                  ├─> Write to filesystem
                  └─> fileAnnounce → Notifies other components
```

### Downlink Flow
```
Component or Ground Command
  └─> FileDownlink (sendFile port or SendFile command)
      └─> Enqueue file in downlink queue
          └─> FileDownlink state machine (Run port driven):
              ├─> Read file chunk
              ├─> Create file packet
              ├─> bufferGet → Get buffer
              ├─> Serialize packet into buffer
              ├─> bufferSendOut → Framer
              │     └─> ByteStreamDriver (e.g., TCP)
              │           └─> Ground System
              └─> After file complete: COOLDOWN state
```

## File Transfer Reliability

### Error Detection
- **Sequence index:** Detects missing/out-of-order packets
- **Checksum:** Detects corruption (END packet)
- **Packet validation:** Each packet type has expected format

### Error Recovery
- **Uplink:** Retry file transfer from ground
- **Downlink:** Re-send file via SendFile command
- **CANCEL packets:** Allow clean abort of bad transfers

### File Corruption Prevention
- Uplink writes to temporary file, renames on success (project-specific)
- Checksum validation before file completion
- File system sync/flush after writes

## File Transfer Best Practices

**Packet sizing:**
- Balance between overhead and latency
- Typical: 512-2048 bytes for space links
- Consider link MTU and framing overhead

**Cooldown tuning:**
- Too short: Saturates link, blocks other traffic
- Too long: Wastes bandwidth, slow file transfer
- Typical: 1-10 seconds depending on link bandwidth and file sizes

**Queue depth:**
- Deep queue: More files can be pending, but uses more memory
- Shallow queue: Conserves memory, but may reject requests during high load
- Typical: 5-20 files

**File validation:**
- Always verify checksums after uplink
- Consider additional file format validation for critical files
- Use FileManager to check file size after uplink

**Uplink priorities:**
- Critical files (software updates): High priority, validate immediately
- Housekeeping files (logs): Lower priority, can wait for available bandwidth

**Downlink priorities:**
- Event logs: High priority (needed for anomaly investigation)
- Science data: Medium priority
- Housekeeping: Lower priority

**How to apply:**
- Size file packets based on link characteristics
- Configure cooldown based on link bandwidth and traffic patterns
- Monitor file transfer completion events
- Implement retry logic in ground system for failed transfers
- Consider file compression for large files (project-specific)
- Log all file operations for traceability
- Use partial downlink (SendPartial) for large files to prioritize important sections
