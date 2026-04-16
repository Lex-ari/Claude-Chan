---
name: F Prime Build and Test Commands
description: Standard commands for F Prime development environment setup, building, and testing components
type: reference

---
## Environment Setup

**Activate F Prime Python virtual environment:**
```bash
cd /path/to/fprime/workspace
source .venv/bin/activate
```

**Note:** The `.venv` directory is typically at the workspace root, not in the `lib/fprime` subdirectory.

## Building Components

**Generate build cache (first time or after .fppi/.fpp changes):**
```bash
fprime-util generate --ut
```

**Build specific component unit tests:**
```bash
# From fprime root directory
fprime-util build --ut lib/fprime/Svc/ComponentName

# Or use ninja directly in build directory
cd build-fprime-automatic-native-ut
ninja Svc_ComponentName_ut_exe
```

**Build all unit tests:**
```bash
fprime-util build --ut
```

## Running Tests

**Run specific component tests:**
```bash
# Using fprime-util (handles paths automatically)
fprime-util check lib/fprime/Svc/ComponentName --ut

# Or run executable directly
cd build-fprime-automatic-native-ut
./bin/Linux/Svc_ComponentName_ut_exe
```

**Run specific test cases with gtest filter:**
```bash
./bin/Linux/Svc_ComponentName_ut_exe --gtest_filter="*test_pattern*"
```

**Run all tests matching a pattern:**
```bash
./bin/Linux/Svc_ComponentName_ut_exe --gtest_filter="*cmd_*"
```

**List available tests:**
```bash
./bin/Linux/Svc_ComponentName_ut_exe --gtest_list_tests
```

## Common Build Directories

- **Unit tests:** `build-fprime-automatic-native-ut/`
- **Regular builds:** `build-fprime-automatic-native/`
- **Test executables:** `build-fprime-automatic-native-ut/bin/Linux/`

## Troubleshooting

**If fprime-util fails to find build cache:**
- Run from the fprime directory (not workspace root)
- Or specify the full path: `fprime-util build --ut lib/fprime/Svc/Component`

**If autocoded files are out of date:**
- Regenerate with: `fprime-util generate --ut`
- Then rebuild: `fprime-util build --ut`

**If using ninja directly:**
- Always run from the build directory
- Use full target name: `ninja Svc_ComponentName_ut_exe`
