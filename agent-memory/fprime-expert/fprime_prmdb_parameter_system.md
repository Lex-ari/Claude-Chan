---
name: F Prime PrmDb Parameter Database System
description: PrmDb parameter storage, file format, get/set protocol, and parameter persistence
type: reference
---

# Svc::PrmDb Parameter Database System

## Location
- SDD: `fprime/Svc/PrmDb/docs/sdd.md`
- FPP: `fprime/Svc/PrmDb/PrmDb.fpp`

## Purpose
Stores parameter values in serialized form, loads from file on startup, provides get/set interface, and saves to file on command.

## Component Type
**Active component** - Has own thread and message queue

## Key Ports

### Input Ports
- `getPrm: Fw.PrmGet (guarded input)` - Components request parameter values
- `setPrm: Fw.PrmSet (async input)` - Components update parameter values

## Parameter File Format

### Field Structure (per parameter entry)

| Field | Size (bytes) | Value |
|-------|--------------|-------|
| Entry Delimiter | 1 | 0xA5 |
| Record Size | 4 | Size of (Parameter ID + Parameter Value) |
| Parameter ID | sizeof(FwPrmIdType) | Parameter ID |
| Parameter Value | Variable | Serialized parameter bytes |

**File Structure:**
```
[Entry 0: Delimiter + Size + ID + Value]
[Entry 1: Delimiter + Size + ID + Value]
...
[Entry N: Delimiter + Size + ID + Value]
[CRC: 4 bytes]
```

## Internal Data Structure

**Table:** Mutex-protected table indexed by parameter ID

**Entry Structure:**
```cpp
struct PrmEntry {
    bool valid;           // Parameter has been loaded
    FwPrmIdType id;       // Parameter ID
    Fw::ParamBuffer val;  // Serialized parameter value
};
```

**Size:** Configurable, must hold all parameters in system

## Parameter Load Flow

**Command:** `PRM_LOAD_FILE` or initialization call

**Algorithm:**

1. **Open parameter file**
2. **For each entry:**
   - Read and verify delimiter (0xA5)
   - Read record size
   - Read parameter ID
   - Read parameter value (serialized)
   - Store in table at index = parameter ID
   - Set `valid = true`
3. **Read and verify CRC**
4. **On error:**
   - Set affected entry as `valid = false`
   - Continue processing (partial load)

**Error Handling:** Graceful degradation - invalid entries return `PARAM_INVALID` on get

## Parameter Get Flow

**Handler:** `getPrm_handler(portNum, id, val)`

**Port Type:** Guarded input (synchronous, mutex protected)

**Algorithm:**

1. **Lock mutex**
2. **Look up parameter by ID in table**
3. **If valid:**
   - Copy serialized value to output buffer
   - Return `Fw::ParamValid::VALID`
4. **If invalid:**
   - Return `Fw::ParamValid::INVALID`
5. **Unlock mutex**

**Called During:** Component initialization after `loadParameters()` command

## Parameter Set Flow

**Handler:** `setPrm_handler(portNum, id, val)`

**Port Type:** Async input (queued)

**Algorithm:**

1. **Lock mutex** (handler is queued but needs protection)
2. **Look up parameter by ID in table**
3. **Update entry:**
   ```cpp
   entry.id = id;
   entry.val = val;
   entry.valid = true;
   ```
4. **Unlock mutex**

**Note:** In-memory update only, not persisted until save command

**Triggered By:** Component receiving parameter update command

## Parameter Save Flow

**Command:** `PRM_SAVE_FILE`

**Algorithm:**

1. **Open parameter file for writing**
2. **For each entry in table:**
   - Write delimiter (0xA5)
   - Write record size
   - Write parameter ID
   - Write serialized parameter value
3. **Compute CRC of entire file**
4. **Write CRC to end of file**
5. **Close file**

**Result:** Overwrites old parameter file with current in-memory values

## Component Parameter Integration

### Component Side (Auto-Generated)

**Parameter Definition (FPP):**
```fpp
param MY_PARAM: F32 default 1.0
```

**Auto-Generated Methods:**
```cpp
void parameterUpdated(FwPrmIdType id);      // Called after param updated
void parametersLoaded();                     // Called after all params loaded
Fw::ParamValid paramGet_MY_PARAM(F32& val);  // Get current value
void paramSet_MY_PARAM(F32 val);             // Set new value
```

**Parameter Update Command (Auto-Generated):**
```cpp
async command MY_PARAM_SET(val: F32)
```

**Flow for Parameter Update Command:**
1. Component receives `MY_PARAM_SET` command
2. Deserializes value from command arguments
3. Calls `PrmSet_out(id, serializedValue)` → PrmDb.setPrm
4. PrmDb stores in table
5. PrmDb calls `PrmSet_out()` back to component (if wired)
6. Component calls `paramSet_MY_PARAM(val)`
7. Component calls `parameterUpdated(id)` callback

**Flow for Parameter Load at Startup:**
1. Ground sends `PRM_LOAD_FILE` to PrmDb
2. PrmDb loads from file into table
3. Ground sends `<component>.LOAD_PARAMETERS` to each component
4. Component calls `PrmGet_out(id)` for each parameter → PrmDb.getPrm
5. PrmDb returns value from table
6. Component calls `paramSet_MY_PARAM(val)` for each
7. Component calls `parametersLoaded()` callback

## Database Types (Staging Feature)

**Enum:** `PrmDbType`
- `DB_ACTIVE` - Active database
- `DB_STAGING` - Staging database

**Purpose:** Allows loading new parameters without affecting active set

**File Load State:** `PrmDbFileLoadState`
- `IDLE` - No load in progress
- `LOADING_FILE_UPDATES` - Loading to staging
- `FILE_UPDATES_STAGED` - Staging complete, can activate

## Error Handling

### Read Errors (PrmReadError enum)
- `OPEN` - Can't open file
- `DELIMITER`, `DELIMITER_SIZE`, `DELIMITER_VALUE` - Delimiter errors
- `RECORD_SIZE`, `RECORD_SIZE_SIZE`, `RECORD_SIZE_VALUE` - Size errors
- `PARAMETER_ID`, `PARAMETER_ID_SIZE` - ID errors
- `PARAMETER_VALUE`, `PARAMETER_VALUE_SIZE` - Value errors
- `CRC`, `CRC_SIZE`, `CRC_BUFFER` - CRC errors
- `SEEK_ZERO` - Seek error

### Write Errors (PrmWriteError enum)
- Similar structure for write operations

**Event Emission:** Detailed events for each error type

## Critical Design Patterns

### 1. Serialized Storage
- Parameters stored in serialized form (`Fw::ParamBuffer`)
- Type-agnostic storage (like TlmChan)
- Component handles serialization/deserialization

### 2. Synchronous Get, Asynchronous Set
- `getPrm` is guarded (synchronous) - Called during initialization, must complete
- `setPrm` is async (queued) - Called during operations, can be deferred
- Both protected by mutex for thread safety

### 3. Partial Load Resilience
- File load continues even if individual entries fail
- Failed entries marked as invalid
- Components can detect invalid parameters on get

### 4. Explicit Save Semantics
- Updates to PrmDb are in-memory only
- Must send `PRM_SAVE_FILE` command to persist
- Allows parameter experimentation without commitment

### 5. Table-Based Storage
- Simple array indexed by parameter ID
- O(1) lookup time
- Requires parameter IDs to be small contiguous integers

### 6. CRC Protection
- Entire file protected by CRC at end
- Detects file corruption
- Validates before loading

## Common Parameter Workflow

### Nominal Startup:
1. PrmDb initialized
2. Ground → `PrmDb.PRM_LOAD_FILE` (load parameters from disk)
3. For each component:
   - Ground → `Component.LOAD_PARAMETERS`
   - Component requests each parameter via `getPrm`
   - Component receives values
   - Component calls `parametersLoaded()` callback

### Parameter Update:
1. Ground → `Component.PARAM_SET` command
2. Component updates internal value
3. Component → `PrmDb.setPrm` (update database)
4. PrmDb stores in memory

### Parameter Persistence:
1. Ground → `PrmDb.PRM_SAVE_FILE`
2. PrmDb writes entire table to file
3. Parameters persist across reboot

### Parameter Reload:
1. Ground → `PrmDb.PRM_LOAD_FILE` (reload from disk)
2. For each component:
   - Ground → `Component.LOAD_PARAMETERS`
   - Component re-reads all parameters

**How to apply:** When adding parameters:
1. Ensure PrmDb table is sized for all parameter IDs in system
2. Always send `PRM_SAVE_FILE` after updating parameters to persist
3. Understand that parameter updates are not saved until explicitly commanded
4. Components must call `loadParametersPort_out()` during init to load parameters
