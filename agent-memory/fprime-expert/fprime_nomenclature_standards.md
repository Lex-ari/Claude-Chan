---
name: F Prime Nomenclature Standards
description: Official naming conventions for F Prime and FPP in documentation and code
type: reference
---

# F Prime Nomenclature Standards

Official representations for F Prime ecosystem in documentation and code.

## F Prime Framework Name

### Long Form: "F Prime"
- **Application:** All communication
- **Format:** Capital F, space, capital P
- **Examples:** "F Prime framework", "Using F Prime"
- **Avoid:** "f prime", "FPrime" (no space), "f-prime", "F_prime"

### Short Form (Formal): "F′"
- **Application:** Presentations, papers, posters, user guides, proposals
- **Format:** Capital F followed by prime symbol (′)
- **How to insert:** 
  - Word/PowerPoint: Insert → Symbol → select prime symbol
  - LaTeX: `F$'$` or `F\prime`
- **Examples:** "The F′ architecture", "F′ components"

### Short Form (Informal): "F'"
- **Application:** Informal communication, email, code comments
- **Format:** Capital F followed by apostrophe
- **Examples:** "F' is great", "F' component"
- **Why:** Apostrophe easier to type than prime symbol

### Software Token: "fprime"
- **Application:** Software identifiers, repository names, file names, package names
- **Format:** All lowercase, no spaces
- **Examples:** `fprime`, `fprime-util`, `fprime-gds`, `libfprime`
- **Why:** Software tokens can't have spaces or special characters

## Usage Guidelines

### First Use in Formal Documents
Use long form ("F Prime") on first mention, then short form:

> "F Prime (F′) is a component-based framework... The F′ architecture provides..."

### Headers and Banners
Use long form only where likely seen first time by wide audience:

> "F Prime Framework User Guide" (not "F′ Framework User Guide")

### Subsequent Mentions
Short form acceptable after first use:

> "F′ components communicate via ports"

### Code and Technical Writing
Informal short form common in code comments:

```cpp
// F' component implementation
// Sends data out F' ports
```

Software tokens in code:
```python
import fprime
from fprime_gds import gds
```

## FPP Language Name

### Long Form: "F Prime Prime"
- **Application:** All communication
- **Acceptable verbal:** "F double-prime" (informal spoken only, not in writing)

### Short Form: "FPP"
- **Application:** All communication (writing and speaking)
- **Examples:** "FPP modeling language", "FPP compiler", "FPP specification"

### Why Not "F′′"?
FPP used instead of F′′ for clarity - easier to distinguish from F′.

## Example Document Usage

```
# F Prime User Guide

F Prime (F′) is a component-based framework developed at NASA JPL.
The F′ architecture consists of components connected via ports.

Components are modeled using F Prime Prime (FPP), which generates
C++ base classes. FPP provides a domain-specific language for
defining components, ports, and topologies.

To install F Prime:
    pip install fprime-tools
    fprime-util new --project MyProject
```

## Common Mistakes to Avoid

| Incorrect | Correct | Context |
|-----------|---------|---------|
| FPrime | F Prime | Long form (has space) |
| f prime | F Prime | Always capital |
| F-prime | F Prime | No hyphen |
| f' | F' | Capital F |
| Fprime | fprime | Software token (all lowercase) |
| F'' | FPP | Use FPP, not F'' |
| F double-prime | F Prime Prime | In writing (spoken okay) |

## How to apply

1. **Documentation:** First use "F Prime", subsequent "F′" (formal) or "F'" (informal)
2. **Code/repos:** Use "fprime" lowercase token
3. **Presentations:** Use "F Prime" in title, "F′" in body
4. **Emails:** "F'" acceptable (apostrophe easier)
5. **FPP language:** Always "FPP" in writing (can say "F double-prime" verbally)
6. **Headers:** "F Prime" in major headers for visibility
7. **Consistency:** Pick one style for document and stick with it
