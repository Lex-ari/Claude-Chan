---
name: Agent Workflow for Changes
description: Repository detection and specialized agent selection for project/Fpy/F Prime work with mandatory code review
type: feedback
---

Always check repository context first, delegate to appropriate specialized agents, and validate with code review.

**Why:** Different repositories and frameworks require specialized domain knowledge. Project repositories have specific patterns, while Fpy and F Prime have deep technical requirements. Repository-specific agents understand project conventions. Framework agents (fpy-expert, fprime-expert) have technical depth. Code review ensures quality and correctness.

**How to apply:**

**STEP 1: Repository Detection (ALWAYS FIRST)**
- Run `git remote -v` to check the repository context
- Check for project-specific patterns and conventions

**STEP 2: Framework-Specific Work**

1. **Fpy-related changes** → Use **fpy-expert** agent:
   - Fpy language features or syntax
   - Fpy compiler changes (parsing, AST, code generation)
   - Fpy bytecode generation
   - .fpy file modifications
   - Fpy compilation pipeline issues

2. **F Prime-related changes** → Use **fprime-expert** agent:
   - F Prime component modifications (FpySequencer, CommandDispatcher, etc.)
   - F Prime port connections or topology
   - F Prime component handlers
   - Integration between Fpy and F Prime components

**STEP 3: Code Review (ALWAYS REQUIRED)**

3. **Code review is mandatory** → Use **fprime-code-review-agent**:
   - **Always** review changes/suggestions from any expert agent
   - Use BOTH the relevant expert agent AND fprime-code-review-agent
   - Validates code quality, error handling, resource management, testability
   - Ensures implementations follow good software engineering practices

**Execution order:**
1. Check `git remote -v` for repository context
2. Apply repository-specific agent if applicable
3. Apply framework-specific agent if needed (fprime-expert or fpy-expert)
4. For code reviews, use both the relevant expert agent AND fprime-code-review-agent

**Workflow examples:**
- Project repo + Fpy change → project-expert + fpy-expert → fprime-code-review-agent
- Project repo + F Prime change → project-expert + fprime-expert → fprime-code-review-agent
- Generic repo + Fpy change → fpy-expert → fprime-code-review-agent
- Generic repo + F Prime change → fprime-expert → fprime-code-review-agent

**Do not** implement changes directly without using the specialized agents when the change is related to project-specific/Fpy/F Prime work.
