---
name: Debugging Methodology and Performance Optimization
description: Strategies for efficient debugging - verify current state first, targeted investigation, systematic verification
type: feedback

---
Always verify the current state of the code before forming hypotheses or explanations, especially when the user mentions they made a change.

**Why:** When debugging after someone mentions "I changed X", assuming old behavior or not checking the actual current state wastes time explaining outdated scenarios. In one case, assumed pushArgsToStack still had size-checking logic when it had been removed, leading to incorrect initial analysis.

**How to apply:**
1. **When user mentions a change**: Immediately read the changed file/function to see current state before theorizing
2. **Start with direct verification**: If debugging why test X fails, read test X first, then read the code it's testing
3. **Use targeted searches**: Search for specific functions/patterns rather than reading entire state machines hoping to find the issue
4. **Think about parallel paths**: If fixing one test case, immediately consider if similar test cases exist with same behavior
5. **Always verify**: Run the specific failing test, then run the full suite to catch regressions

**Systematic investigation flow:**
- Read error message → Read the test → Read the code being tested → Form hypothesis → Verify hypothesis → Fix → Test specific case → Test full suite

**Don't:**
- Form elaborate theories based on assumed code state
- Read through large files hoping to stumble on the issue
- Fix one thing without considering related code paths
