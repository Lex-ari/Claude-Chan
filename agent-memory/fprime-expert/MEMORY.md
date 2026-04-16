# F' Framework Expert Memory Index

Core F' framework knowledge for understanding NASA JPL's flight software framework.

## Overview
- [F' Comprehensive Overview](fprime_overview.md) — High-level framework summary, philosophy, key subsystems

## Framework Architecture
- [F' Architecture](fprime_architecture.md) — Directory structure, module organization, framework philosophy
- [Component Model](fprime_component_model.md) — Passive/queued/active, threading, queues, execution contexts, initialization
- [Port System Detailed](fprime_ports_detailed.md) — Port design vs instantiation, serialization, arrays, connection rules
- [Component Types and Threading](component_types.md) — Legacy entry, see Component Model for comprehensive version
- [Port Patterns](port_patterns.md) — Sync/async/guarded ports, invocation patterns, thread safety

## Core Data Constructs
- [Data Constructs](fprime_data_constructs.md) — Commands, events, channels, parameters: properties, flow, patterns
- [Data Types Comprehensive](fprime_datatypes_comprehensive.md) — Primitives, enums, arrays, serializables, PolyType, strings, buffers

## Command and Control
- [Commanding System](commanding_system.md) — CmdDispatcher, registration, dispatch flow, response handling
- [Sequencing Detailed](fprime_sequencing_detailed.md) — Architecture, validation, execution modes, timing, off-nominal
- [Sequencer System](sequencer_system.md) — Legacy entry, see Sequencing Detailed for comprehensive version

## Telemetry and Events
- [Event System](event_system.md) — Event severity, Fw::Log ports, ActiveTextLogger, dual paths
- [Telemetry System](telemetry_system.md) — TlmChan, hash table storage, periodic downlink, change detection
- [Parameter System](parameter_system.md) — PrmDb, file persistence, load/save flow, callbacks

## Scheduling and Timing
- [Rate Group System](rate_group_system.md) — RateGroupDriver dividers, ActiveRateGroup, cycle slip detection

## System Services
- [Health Monitoring](health_monitoring.md) — Ping mechanism, timeout tracking, watchdog stroking
- [File Management](file_management.md) — FileUplink/Downlink, packet-based transfer, checksum validation

## Development and Implementation
- [Development Workflow](fprime_development_workflow.md) — Complete process: requirements to integration testing, tools, best practices
- [Topology Construction](fprime_topology_construction.md) — Instantiation, init, interconnection, command registration, startup sequence
- [Autocoding Patterns](fprime_autocoding_patterns.md) — Generated functions, handler signatures, naming conventions, lifecycle hooks

## Implementation Patterns
- [Serialization Patterns](serialization_patterns.md) — Fw::Serializable, buffer types, endianness, versioning
- [State Management](state_management.md) — Thread safety, mutexes, guarded ports, state persistence
- [Memory Management Patterns](fprime_memory_patterns.md) — Initialization allocation, runtime buffer pools, flight software safety

## Testing
- [Unit Testing Framework](fprime_unit_testing_framework.md) — TesterBase, GTestBase, assertion macros, testing patterns and best practices

## Standards and Conventions
- [Nomenclature Standards](fprime_nomenclature_standards.md) — Official naming: F Prime vs F′ vs fprime, FPP usage, documentation style

## Quick Reference
- [Quick Reference Guide](quick_reference_guide.md) — Fast lookup of critical facts, patterns, and common gotchas
