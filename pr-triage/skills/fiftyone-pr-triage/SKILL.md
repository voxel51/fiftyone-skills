---
name: fiftyone-pr-triage
description: Triage FiftyOne GitHub issues by validating status, categorizing resolution, and generating standardized responses. Use when reviewing issues to determine if fixed, won't fix, not reproducible, no longer relevant, or still valid.
---

# FiftyOne Issue Triage

## Categories

| Category | When to Use |
|----------|-------------|
| **Already Fixed** | Resolved in recent commits/releases |
| **Won't Fix** | By design, out of scope, or external behavior (e.g., browser, OS) |
| **Not Reproducible** | Cannot reproduce with provided info |
| **No Longer Relevant** | Outdated version, deprecated feature, or stale (6+ months) |
| **Still Valid** | Confirmed bug or valid feature request needing work |

## Workflow

### 1. Fetch Issue
```bash
gh issue view {number} --repo voxel51/fiftyone --json title,body,author,state,labels,comments
```

### 2. Analyze
- Extract: issue type, version, reproduction steps, error message
- Search related: `gh issue list --repo voxel51/fiftyone --state all --search "keyword"`
- Check git history: `git log --oneline --grep="keyword"`

### 3. Assess Responsibility

```
Is this FiftyOne's responsibility?
├─ External behavior (browser, OS, third-party)? → Won't Fix
├─ User workflow/configuration issue? → Won't Fix (with workaround)
└─ FiftyOne code/behavior issue? → Continue assessment
```

### 4. Assess Value (before proposing fixes)

Ask: "Is a fix/doc change worth the effort?"
- How many users affected?
- Is workaround simple?
- Would fix add complexity or hurt performance?

### 5. Check Documentation

Before closing, verify if behavior is documented:
```bash
grep -r "keyword" docs/source/ --include="*.rst"
```

### 6. Categorize and Respond

## Decision Tree

```
Issue reported
    │
    ├─ External/not FiftyOne's responsibility? → Won't Fix
    │
    ├─ Can reproduce?
    │   └─ NO → Not Reproducible
    │
    ├─ Fixed in recent commit/release? → Already Fixed
    │
    ├─ By design or out of scope? → Won't Fix
    │
    ├─ Old version, stale, deprecated? → No Longer Relevant
    │
    └─ Confirmed, needs work → Still Valid
```

## Response Templates

**Tone:** Always start with thanks, be friendly, then explain.

### Won't Fix (External Behavior)
```markdown
Hi @{author},

Thanks for reporting this and for the detailed description!

This is {expected behavior / external to FiftyOne}. {Brief explanation}.

**Quick fixes:**
- {Workaround 1}
- {Workaround 2}

Closing as this is {external behavior}, but hopefully this helps!
```

### Already Fixed
```markdown
Hi @{author},

Thanks for reporting! This was fixed in {version/PR}.

**To resolve:**
pip install --upgrade fiftyone

Let us know if the issue persists.
```

### Not Reproducible
```markdown
Hi @{author},

Thanks for reporting! We couldn't reproduce this with the provided info.

**Could you provide:**
1. Minimal reproducible example
2. Complete error traceback
3. Sample data (if applicable)

We'll reopen once we can reproduce.
```

### Still Valid
```markdown
Hi @{author},

Thanks for reporting! Confirmed this issue.

**Root cause:** {technical explanation}

**Location:** `{filepath}:{line}`

{Next steps or suggested fix}
```

## Quick Reference

| Category | Key Indicator | Action |
|----------|---------------|--------|
| Already Fixed | Found in git log | Point to PR, suggest upgrade |
| Won't Fix | External/by design | Explain, provide workaround |
| Not Reproducible | Can't reproduce | Request more info |
| No Longer Relevant | Old/stale/deprecated | Explain, suggest new issue |
| Still Valid | Confirmed, no fix | Document root cause, propose fix |

## Checklist

- [ ] Read full issue + comments
- [ ] Check if external/FiftyOne responsibility
- [ ] Search codebase for related code
- [ ] Check git history for recent fixes
- [ ] Search closed issues for duplicates
- [ ] Check if documented
- [ ] Assess value of potential fix
- [ ] Attempt reproduction (if bug)
- [ ] Trace user's reproduction steps in source code
- [ ] Verify workarounds work by checking actual code path
- [ ] Keep user response simple (no internal code details)
- [ ] End with 1-2 sentence internal summary

## If User Willing to Contribute

When user indicates willingness to contribute, after validating the issue provide:

- **Contribution guide:** https://docs.voxel51.com/contribute/index.html
- **Discord:** https://discord.com/invite/fiftyone-community (#github-contribution channel)
- Point to relevant code files for the fix
