---
name: Unit Test Writing Methodology
description: Process for writing unit tests by analyzing existing tests and following established patterns
type: feedback

---
When writing unit tests for any codebase, follow this methodology:

**Step 1: Read Existing Tests**
- Locate similar test files in the component's test directory
- Read 2-3 reference tests that are closest to the functionality being tested
- Identify the test structure, naming conventions, and assertion patterns

**Step 2: Keep Tests Simple**
- Write the minimal test that verifies the behavior
- Don't add extra features, edge cases, or "improvements" beyond what's requested
- Match the complexity level of existing tests

**Step 3: Follow Existing Style**
- Use the same naming convention (e.g., `TEST_F`, `cmd_COMMAND_NAME`)
- Copy the structure: setup → action → assertions → cleanup
- Use the same helper functions and assertion macros
- Match comment style (terse vs verbose)
- Follow the same variable naming patterns

**Step 4: Match Test Patterns**
- If testing a command with args, look at other arg tests
- If testing error cases, look at other error tests
- Copy the assertion order from reference tests
- Use the same state transition checks

**Step 5: Verify with Agents**
- Use fprime-expert for F' component behavior understanding
- Use fpy-expert for Fpy bytecode and sequencer specifics
- Use fprime-code-review-agent to catch missing assertions or style issues

**Why:** This approach ensures tests integrate seamlessly with existing test suites, are maintainable by the team, and don't introduce inconsistencies.

**How to apply:** Before writing any test, spend time reading the existing test file. Let the patterns guide the implementation rather than inventing new approaches.
