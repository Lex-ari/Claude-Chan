---
name: F' Parameter System Architecture
description: Parameter storage and management including PrmDb component and Fw::Prm ports
type: reference
---

# F' Parameter System Architecture

The F' parameter system enables components to have configurable values that persist across reboots and can be updated via commands.

## Parameter Port Types

### Fw::PrmGet Port (Fw/Prm/docs/sdd.md)

**Purpose:** Retrieve a parameter value from storage

**Arguments:**
- `id` (FwPrmIdType): Parameter ID
- `buff` (Fw::PrmBuffer): Target buffer for parameter value (output)

**Return values:**
- `PARAM_VALID`: Parameter successfully retrieved
- `PARAM_INVALID`: Parameter not successfully retrieved
- `PARAM_UNINIT`: Parameter hasn't been initialized (component-only, not returned by port)
- `PARAM_DEFAULT`: Default value used (component-only, indicates PARAM_INVALID was returned)

### Fw::PrmSet Port (Fw/Prm/docs/sdd.md)

**Purpose:** Update a parameter value in storage

**Arguments:**
- `id` (FwPrmIdType): Parameter ID
- `buff` (Fw::PrmBuffer): Buffer containing serialized parameter value

**Return:** Status (success/failure)

### Fw::PrmBuffer Serializable

The `Fw::PrmBuffer` class stores serialized parameter values. This allows the framework to store parameters without knowing their types.

## Svc::PrmDb Component (Svc/PrmDb/docs/sdd.md)

**Purpose:** Store parameter values in memory and persist to/from file

**Requirements:**
- PRMDB-001: Load parameter values from a file
- PRMDB-002: Provide interface to read parameter values
- PRMDB-003: Provide interface to update parameter values
- PRMDB-004: Provide command to save current parameter values

**Ports:**
- `getPrm` (input, sync): Get a parameter value (Fw::PrmGet)
- `setPrm` (input, async): Update a parameter value (Fw::PrmSet)

**Commands:**
- `PRM_SAVE_FILE`: Save entire parameter table to file

**Key behaviors:**
- Stores parameters in **mutex-protected table** indexed by parameter ID
- Loads parameters from file during initialization
- Returns `PARAM_INVALID` for parameters not loaded from file
- Updates in memory when `setPrm` called; file NOT updated until `PRM_SAVE_FILE` command
- File updates overwrite old values; unsaved updates lost on restart

**Parameter file format:**
Each parameter entry in file:

| Field | Size (bytes) | Value |
|-------|--------------|-------|
| Entry Delimiter | 1 | 0xA5 |
| Record Size | 4 | ID size + parameter value size |
| Parameter ID | sizeof(FwPrmIdType) | Parameter ID value |
| Parameter Value | variable | Serialized parameter bytes |

**Why:** PrmDb provides persistent configuration storage with atomic file writes. Updates via `setPrm` are fast (memory-only); `PRM_SAVE_FILE` provides controlled persistence.

## Parameter Flow Architecture

### Initialization (Load Parameters)
```
System Initialization
  └─> PrmDb loads parameter file
       ├─ Parse file entries into table
       └─ Set valid flags for loaded parameters

Component Initialization
  └─> loadParameters() [auto-generated]
      └─ For each parameter:
          └─ getPrm port → PrmDb
              └─ If PARAM_VALID: use loaded value
              └─ If PARAM_INVALID: use default value (if specified)
```

### Runtime (Update Parameters)
```
Ground Command
  └─> Component command handler
      └─> Component parameter update
          └─> setPrm port → PrmDb
              └─> Update in-memory table
              └─> Call parameterUpdated() callback [component can override]

Ground Command
  └─> PRM_SAVE_FILE command → PrmDb
      └─> Write entire table to file (overwrites old file)
```

## Parameter Definition Pattern

In component FPP:
```
param MY_THRESHOLD: F32 default 10.0 \
    id 0x100 \
    set opcode 0x10 \
    save opcode 0x11
```

This auto-generates:
- `PRM_SET_MY_THRESHOLD` command to update the parameter
- `PRM_SAVE_MY_THRESHOLD` command to save the parameter to file
- `paramGet_MY_THRESHOLD()` method to read current value
- `parameterUpdated()` callback when parameter changes

In component C++:
```cpp
// Read parameter value
F32 threshold = paramGet_MY_THRESHOLD();

// Override callback for parameter updates (optional)
void MyComponent::parameterUpdated(FwPrmIdType id) {
    if (id == PARAMID_MY_THRESHOLD) {
        // React to parameter change
        F32 newValue = paramGet_MY_THRESHOLD();
        // Update internal state
    }
}

// Override callback after all parameters loaded (optional)
void MyComponent::parametersLoaded() {
    // All parameters have been loaded from file
    // Safe to initialize state that depends on multiple parameters
}
```

## Parameter vs. Telemetry

**Parameters:** Ground → Component (configuration)
**Telemetry:** Component → Ground (state/measurements)

Some components implement "parameter telemetry" pattern:
- Mirror each parameter with a telemetry channel
- Emit parameter value as telemetry when it changes
- Allows ground to verify parameter updates

## Parameter Update Commands

F' auto-generates two commands per parameter:

1. **SET command:** Updates parameter in component AND calls PrmDb
2. **SAVE command:** Tells PrmDb to save that specific parameter to file

Alternatively, use the global `PRM_SAVE_FILE` command to save all parameters at once.

**Why two-step process?**
- Allows parameter tuning without wearing out flash memory
- Operators can try multiple parameter values before committing to file
- Prevents frequent file writes during operations

**How to apply:**
- Use parameters for values that change infrequently (not telemetry-rate)
- Provide sensible default values in FPP definition
- Override `parameterUpdated()` if component needs to react to parameter changes immediately
- Override `parametersLoaded()` if component needs all parameters before initialization
- Document parameter units and valid ranges in comments
- Test both default values and parameter file loading paths
- Remember: parameters NOT saved until PRM_SAVE_FILE or component-specific SAVE command
