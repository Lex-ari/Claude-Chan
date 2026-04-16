---
name: Multi-Pass Adversarial Code Review Methodology
description: Rigorous code review process using multi-agent analysis with verification cycles to eliminate false positives and ensure accuracy
type: feedback

---
**Rule**: When conducting code reviews, use multi-agent analysis with adversarial verification cycles to ensure accuracy and eliminate false positives.

**Why**: Initial code reviews often contain false positives, missed context, and overstated severity because reviewers miss protective code, make assumptions without verification, or claim vulnerabilities without evidence. A single-pass review is insufficient for accurate findings.

**How to apply**:

## Phase 1: Multi-Agent Initial Analysis

Use ALL available specialized agents in parallel:
- **fprime-expert**: For F' framework patterns, component architecture, port handlers
- **fprime-code-review-agent**: For JPL rules, security vulnerabilities, memory safety
- **Explore agent**: For integration impact, topology changes, configuration mismatches
- **project-expert** (if in project repo): For architectural analysis
- **fpy-expert** (if Fpy-related): For sequence language issues

**Requirements**:
- Each agent must provide exact line numbers
- Each agent must include 3-5 lines of code context
- Each agent must cite specific rules/patterns violated
- Each agent must search actual source files (not assume)

## Phase 2: Adversarial Re-Review (Critical)

**Never trust the initial review.** Actively search for reasons why each finding is WRONG:

### Verification Checklist for Each Finding:

1. **Read the actual code** at claimed line numbers
   - Does the vulnerability actually exist?
   - Are line numbers accurate?
   - Is surrounding context considered?

2. **Search for protective code** the review may have missed
   - Are there validation functions upstream?
   - Are there checks at call sites?
   - Are there alternative safe functions?
   - Example: If review claims "unchecked function()", search for other validation functions

3. **Verify the attack path**
   - Can the vulnerability actually be triggered?
   - Are there validations before the call site?
   - Example: If review claims "function() returns NULL", verify if check_funciton() check prevents this

4. **Check for false pattern matching**
   - Did review assume all functions follow same pattern?
   - Example: Claiming all parseEnum functions vulnerable when some use safe helpers
   - Use grep to verify actual patterns across files

5. **Demand evidence for claimed vulnerabilities**
   - Can NULL actually occur despite validation?
   - Is there proof the unsafe path is reachable?
   - Are there test cases demonstrating the issue?

6. **Question severity assessments**
   - Is "CRITICAL" justified or is it actually MEDIUM?
   - Does exploitation require multiple preconditions?
   - Are there mitigations the review missed?

### Red Flags for False Positives:

- ❌ No line numbers provided
- ❌ No code snippets shown
- ❌ Claims without "because [evidence]"
- ❌ Assumes pattern without verifying each instance
- ❌ Ignores validation layers
- ❌ "Can return NULL" without proof it does
- ❌ Severity inflation (calling everything CRITICAL)

## Phase 3: Source Code Verification

For every claimed vulnerability:

1. **Read the actual function** at the claimed line
   ```bash
   sed -n 'START,ENDp' path/to/file.cpp
   ```

2. **Search for the pattern** across the codebase
   ```bash
   grep -n "pattern" file.cpp
   grep -rn "safe_helper_function" .
   ```

3. **Find all call sites** of vulnerable functions
   ```bash
   grep -n "vulnerable_function" file.cpp
   ```

4. **Check for protective wrappers** or validation
   ```bash
   grep -B10 "vulnerable_call" file.cpp  # Check 10 lines before
   ```

5. **Verify claims against libcbor/framework source** if needed
   ```bash
   find . -name "*.c" -exec grep -A10 "function_name" {} \;
   ```

## Phase 4: Document Verified vs False Findings

Create accuracy check document showing:

### For Verified Issues:
- ✅ Line numbers confirmed
- ✅ Code snippet showing issue
- ✅ No protective code found
- ✅ Attack path is reachable
- ✅ Evidence supports severity

### For False Positives:
- ❌ Why review was wrong
- ✅ Protective code that was missed
- ✅ Alternative safe functions
- ✅ Validation layers that prevent exploitation
- ✅ Corrected severity assessment

## Phase 5: Final Report

Merge verified findings with corrections:

**Structure**:
1. Executive Summary (corrected assessment)
2. Verified Issues Requiring Fixes (with evidence)
3. False Positives from Review (with counter-evidence)
4. Optional Improvements (defensive programming)
5. Positive Findings (what code does well)
6. Quick Fix Checklist (ready to implement)

**Accuracy Metrics**:
- State accuracy rate (e.g., "25% of claimed critical issues verified")
- List major errors in review
- Provide corrected risk assessment

## Example: Adversarial Verification in Action

**Initial Claim**: "CRITICAL: function() unchecked, causes configuration corruption"

**Adversarial Questions**:
- Are there other IP validation functions?
- Is the result checked at call site?
- Can corrupted data actually reach hardware?

**Verification**:
```bash
# Search for Enum validation functions
grep -n "convertEnum\|function" MyComponent.cpp

# Found: convertEnumToU32() at line 55 - has validation!
# Found: Line 1641 checks result before use
```

**Verdict**: ❌ FALSE POSITIVE - Safe validation exists and is used

## Key Principles

1. **Trust but verify**: Never assume initial review is correct
2. **Read actual code**: Don't rely on grep output alone
3. **Search for mitigations**: Actively look for protective code
4. **Demand evidence**: "Can return NULL" needs proof, not theory
5. **Question severity**: Most issues aren't CRITICAL
6. **Multiple cycles**: Verify → Counter-verify → Re-verify
7. **Document accuracy**: Show what was wrong and why

## Anti-Patterns to Avoid

- ❌ Accepting line numbers without verification
- ❌ Claiming vulnerabilities without evidence
- ❌ Ignoring validation layers
- ❌ Pattern matching without per-instance verification
- ❌ Severity inflation (calling everything critical)
- ❌ Single-pass review without verification
- ❌ Trusting agent findings without source code confirmation

## Quality Gates

**Do not deliver review unless**:
- ✅ Every line number verified by reading actual code
- ✅ Every "can return NULL" claim backed by evidence
- ✅ Every function claim verified (not pattern-assumed)
- ✅ Protective code searched for and documented
- ✅ False positives identified and corrected
- ✅ Accuracy assessment included

## Success Criteria

Good review has:
- High accuracy rate (>75% of findings verified)
- Documented counter-evidence for false positives
- Corrected severity assessments
- Evidence-backed claims
- Acknowledged protective code
- Realistic risk assessment

Poor review has:
- False positives not identified
- Missing protective code
- Overstated severity
- Claims without evidence
- Assumed patterns without verification
- No accuracy checking

---

**Example Result**: 
- Initial review: "4 CRITICAL issues, UNSAFE TO MERGE"
- After verification: "2 HIGH issues (25 min fix), safe to merge after"
- Accuracy improvement: Eliminated 2 false positives, corrected 2 overstated claims
