---
name: FPP Knowledge Gaps and Expert Boundaries
description: Areas where fpp-expert should consult fprime-expert or defer to documentation, and boundaries of FPP vs F Prime implementation knowledge
type: reference
originSessionId: c7708e45-a599-4300-a457-572b467a90ee
---
# FPP Knowledge Gaps and Expert Boundaries

## When to Consult fprime-expert

### F Prime Framework Implementation Details

**fpp-expert knows:** FPP definitions, generated code structure, interface contracts
**fprime-expert knows:** 
- F Prime C++ framework implementation internals
- Component base class implementations
- Port invocation mechanisms and threading details
- Serialization buffer management
- Framework utility classes (Fw::String, Fw::Buffer, etc.)
- OS abstraction layer details
- Framework initialization and shutdown sequences

**Example boundary:**
- fpp-expert: "FPP generates `cmdHandler_START()` signature"  
- fprime-expert: "How to implement the handler using F Prime buffer APIs"

### Build System Integration

**fpp-expert knows:** What FPP tools do, basic usage patterns
**fprime-expert knows:**
- F Prime CMake infrastructure
- Build target generation
- Cross-compilation setup
- Platform-specific build configurations
- Integration with F Prime's `fprime-util` tool

### Runtime Behavior

**fpp-expert knows:** Static FPP semantics, what code is generated
**fprime-expert knows:**
- Runtime threading behavior
- Message queue mechanics
- Priority scheduling
- Component lifecycle (construction, initialization, task creation)
- Port invocation call stack
- Performance characteristics

### Testing Infrastructure

**fpp-expert knows:** Component structure from FPP perspective
**fprime-expert knows:**
- F Prime unit test harness
- `GTest` integration patterns
- Component test patterns
- Port mocking strategies
- Telemetry/event verification in tests

### Ground System Integration

**fpp-expert knows:** Dictionary generation from FPP
**fprime-expert knows:**
- F Prime Ground Data System (GDS)
- Sequence files and commanding
- Telemetry display and plotting
- Event filtering and alerting
- Parameter database management

## When to Defer to Documentation

### State Machine Implementation Details

**Status:** FPP has state machine definitions but implementation details not fully covered in study.

**What's known:**
- Basic syntax for state machine definitions
- External vs internal state machines
- States, signals, transitions, guards, actions, choices
- Typed elements and type option assignment

**What needs deeper study:**
- Complete semantics of state machine execution
- Guard expression evaluation
- Action execution contexts
- Choice node resolution
- State entry/exit behavior in detail
- Hierarchical state machine behavior (nested states)

**Recommendation:** Consult full specification in `/home/lex/FPrime/fpp/docs/spec/State-Machine-Behavior-Elements/` for state machine implementation questions.

### Data Products (Records and Containers)

**Status:** Basic syntax covered but detailed semantics not fully studied.

**What's known:**
- Record and container specifiers exist
- Used for data product generation
- Require product ports

**What needs deeper study:**
- Data product lifecycle
- Buffer management for data products
- Relationship between records and containers
- Pull vs push models (product get vs product request)

**Recommendation:** Consult data product sections of specification and F Prime data product documentation.

### Telemetry Packet Sets

**Status:** Syntax known but packet generation details limited.

**What's known:**
- Telemetry packet set specifiers in topologies
- Assigns channels to packets

**What needs deeper study:**
- Packet construction and sizing
- Downlink scheduling
- Packet priorities

**Recommendation:** Consult telemetry packet specification and F Prime downlink documentation.

### XML to FPP Conversion

**Status:** Tool exists but detailed mapping not studied.

**What's known:**
- `fpp-from-xml` tool exists
- Converts legacy XML component definitions

**What needs deeper study:**
- Mapping of XML constructs to FPP
- Limitations and manual fixups needed
- Migration strategies for large codebases

**Recommendation:** Use tool with trial and error, consult tool help.

### Format String Details

**Status:** Basic syntax known but complete format specification not studied.

**What's known:**
- Format strings use Python-like syntax
- Basic patterns: `{}`, `{.3f}`, `{x}`, `{d}`

**What needs deeper study:**
- Complete format string grammar
- All supported format specifiers
- Locale and internationalization

**Recommendation:** Consult format string section of specification.

### Advanced Type System Features

**Status:** Most features covered but some edge cases uncertain.

**What needs deeper study:**
- Type option conversion rules in detail
- Anonymous type inference in all contexts
- Alias list traversal edge cases
- Type compatibility for all combinations

**Recommendation:** Consult Types and Type-Checking sections of specification for complex type questions.

## Areas Outside FPP Scope

### C++ Implementation Code

**Not in scope:** Writing C++ component implementations, using F Prime C++ APIs

**FPP provides:** Generated base classes, port signatures, handler signatures

**Implementation requires:** C++ knowledge and F Prime API knowledge (fprime-expert domain)

### Hardware Integration

**Not in scope:** Driver implementation, hardware register access, DMA setup

**FPP provides:** Component and port structure for drivers

**Implementation requires:** Embedded systems knowledge, HAL APIs (fprime-expert domain)

### Operating System Configuration

**Not in scope:** OS task priorities, scheduling policies, resource limits

**FPP provides:** Thread priority and stack size parameters

**Configuration requires:** OS knowledge and platform-specific tuning

### Debugging and Troubleshooting

**Not in scope:** Runtime debugging, analyzing component behavior, fixing threading issues

**FPP provides:** Static model structure

**Debugging requires:** GDB/LLDB knowledge, F Prime runtime understanding

### Performance Optimization

**Not in scope:** Profiling, optimizing component execution, reducing message queue latency

**FPP provides:** Structural definitions

**Optimization requires:** Performance analysis, F Prime runtime knowledge

## Recommended Study for Deeper FPP Knowledge

### High Priority (if needed)
1. State machine behavior elements (complete sections)
2. Expressions section (detailed operator precedence, type conversion)
3. Analysis and translation section (complete compiler pipeline)

### Medium Priority
1. Data product specifiers (records and containers)
2. Telemetry packet sets
3. Advanced topology patterns (subtopologies, interface implementations)

### Low Priority
1. Historical context (XML to FPP evolution)
2. Compiler implementation details (Scala codebase)
3. Native binary compilation (GraalVM)

## Confidence Levels by Topic

### High Confidence (95-100%)
- Basic FPP syntax and lexical elements
- Module and component definitions
- Port definitions and port instances
- Type system (primitives, enums, structs, arrays, aliases)
- Command, event, telemetry specifiers
- Topology definitions and connections
- File conventions (.fpp vs .fppi)
- Tool usage (fpp-check, fpp-to-cpp, fpp-depend, fpp-locate-defs)
- Dependency management workflow

### Medium Confidence (70-95%)
- State machine definitions (basic structure known, execution semantics partial)
- Component instance configuration
- Port matching and auto-numbering
- Connection graph patterns
- Parameter specifiers
- Generated C++ code structure

### Lower Confidence (50-70%)
- Data products (records and containers)
- Telemetry packet sets
- State machine typed elements and type options
- Advanced type conversion rules
- Format string complete specification
- Include path resolution edge cases

### Minimal Confidence (<50%)
- Compiler internals (Scala implementation)
- State machine code generation details
- Native binary compilation process
- Historical XML format details
- Advanced optimization patterns

## Collaboration Protocol

When user asks questions:

1. **FPP language questions** → fpp-expert answers directly with confidence
2. **F Prime framework questions** → fpp-expert provides FPP perspective, suggests consulting fprime-expert
3. **C++ implementation questions** → defer to fprime-expert
4. **Build system questions** → provide FPP tool usage, defer build integration to fprime-expert
5. **Ambiguous questions** → clarify whether question is about FPP model or F Prime implementation

**Always:** Cite specification sections when answering detailed semantic questions
**Always:** Acknowledge uncertainty rather than guessing
**Always:** Distinguish between "what FPP generates" and "how to implement"
