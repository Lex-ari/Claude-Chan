---
name: Code Review Style Preference
description: User's preferred comprehensive code review format with multi-agent analysis, line numbers, and verification
type: user
---

# Code Review Style Preference

The user prefers comprehensive, multi-agent code reviews with the following specific format:

## Multi-Agent Approach

Use multiple specialized agents in parallel:
- **fprime-expert**: F' component architecture, patterns, buffer ownership, port handlers
- **fprime-code-review-agent**: Code quality, JPL rules, security vulnerabilities, memory safety
- **Explore agent**: Topology changes, configuration updates, integration impacts

Run agents concurrently for efficiency, then synthesize findings.

## Document Structure

### 1. Executive Summary
- Overall assessment (REQUIRES FIXES / APPROVED / etc.)
- Count of issues by severity (Critical/High/Medium/Low)
- Brief positive findings summary
- Risk level (integration risk, testing status)

### 2. Table of Contents
Clear navigation to all sections

### 3. Issues by Severity

For each issue, include:

**Header Format**:
```markdown
### 🔴 CRITICAL-X: Brief Title

**Found By**: [agent-name]
**Violates**: [Specific rule - e.g., "JPL Rule #22 (Memory safety)", "F' Pattern - Buffer ownership"]
**Severity**: Critical/High/Medium/Low
**Category**: Security, Safety, Maintainability, Style, etc.
**File**: path/to/file.cpp
**Lines**: Exact line numbers
```

**Problem Code Section**:
```cpp
// File.cpp:433-436 (functionName)
actual code line 1                    // Line 433
actual code line 2                    // Line 434 ⚠️ Issue here
actual code line 3                    // Line 436
```

**Why This is [Severity]**:
- Bullet points explaining impact
- Security/safety implications
- What can go wrong

**Recommended Fix** (with line numbers):
```cpp
// File.cpp:433-436 - Apply fix here
corrected code line 1                 // Line 433
// ADD THIS:
new validation logic
corrected code line 2                 // Line 434
```

### 4. Positive Findings Section

Include "✅ What's Good" section:
- **Found By**: [agent-name]
- **Follows**: [Rule/pattern it correctly follows]
- Code examples of good patterns
- Line numbers where good patterns appear
- Reinforcement of correct practices

### 5. Architecture & Design Review

- Architectural concerns beyond code-level issues
- Threading models
- Component interactions
- Design patterns used

### 6. Non-Primary Changes

Review scope beyond main changes:
- Topology modifications
- Configuration changes
- Sequence updates
- Build system changes
- Other components affected

### 7. Recommendations Section

Organized by priority:
- **Must Fix Before Merge** (Critical/High)
- **Should Fix** (Medium)
- **Nice to Have** (Low)
- **Testing Recommendations**
- **Integration Review** needs

## Key Principles

### Specificity
- **Always include exact line numbers** in code blocks as comments
- Show 3-5 lines of context around problematic code
- Reference actual variable names, function names from the code
- Cite specific rules violated (JPL Rule #X, F' Pattern, CLAUDE.md section)

### Attribution
Every finding must show:
1. Which agent/tool found it
2. Which coding standard/rule it violates
3. Why that rule exists (security, safety, maintainability)

### Verification
After generating review:
1. Read actual source code for each finding
2. Verify line numbers are correct
3. Verify issue exists as described
4. Check for false positives
5. Document verification results

### Dual Perspective
Include both:
- **Problems**: What's wrong and needs fixing
- **Successes**: What's done well and should continue

### Actionability
For each issue:
- Exact file and line number
- Show current problematic code
- Show recommended fix with line numbers
- Explain why the fix works

## File Naming

- Review document: `CODE_REVIEW_[TICKET-ID].md`
- Verification document: `CODE_REVIEW_VERIFICATION.md`

## Markdown Formatting

- Use emoji severity indicators: 🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low
- Use ✅ for verified/positive findings
- Use ⚠️ inline to mark problematic lines
- Use code blocks with language hints: ```cpp, ```fpp, ```bash
- Use tables for summaries
- Use `> blockquotes` for important notes

## Severity Guidelines

**Critical**: 
- Security vulnerabilities (null pointer dereference, buffer overflow, injection)
- Safety issues that could cause spacecraft harm
- Memory corruption from untrusted input

**High**:
- Resource leaks that degrade system over time
- API contract violations
- Data races / thread safety issues
- Array bounds issues

**Medium**:
- Code duplication (DRY violations)
- Missing validation (DoS resilience)
- Magic numbers
- Style violations that impact maintainability
- Architecture inconsistencies

**Low**:
- Minor style violations (cast style, naming)
- Missing documentation
- POSIX compliance (newlines at EOF)

## Special Considerations for F' Code

### Always Check
- Buffer ownership and deallocation in all code paths
- Port handler patterns (sync vs async)
- Component state management and thread safety
- Event severity appropriateness
- Telemetry naming conventions (snake_case for non-parameters)
- External data as untrusted input
- CSPICE thread safety (SPICEErrorHandler usage)

### Reference Standards
- JPL Power of 10 Rules
- F' Framework patterns (from fprime.jpl.nasa.gov)
- Project CLAUDE.md and CLAUDE_DOCS/
- NASA flight software best practices

## Output Format

Generate two documents:
1. `CODE_REVIEW_[ID].md` - The comprehensive review
2. `CODE_REVIEW_VERIFICATION.md` - Evidence that each finding was verified against actual code

## Why This Style Works

- **Line numbers**: Makes fixes actionable, no guessing where to look
- **Agent attribution**: Shows methodology, builds trust in findings
- **Rule violations**: Educates developers on standards
- **Verification**: Ensures accuracy, no false positives
- **Positive findings**: Reinforces good practices, not just criticism
- **Comprehensive**: Catches issues at code, architecture, and integration levels
- **Prioritized**: Clear what must be fixed vs. nice-to-have
