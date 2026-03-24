---
name: fiftyone-eval-plugin
description: Evaluates FiftyOne plugins for quality, security, and agent-readiness. Use when reviewing a plugin before installation, auditing an existing plugin, validating a plugin you just built, or assessing community plugins for safety. Produces a structured report with scores and actionable recommendations.
---

# Evaluate FiftyOne Plugins

## Key Directives

**ALWAYS follow these rules:**

### 1. Read the entire plugin before judging
Read every source and configuration file of the plugin. Common file extensions: `.py`, `.ts`, `.tsx`, `.js`, `.yaml`, `.yml`, and `.json`. Never construct an assessment of a plugin without first reading every line of every source file.

### 2. Security first
Check for dangerous patterns before anything else. A plugin with perfect code quality that violates established and well known security best practices, is an immediate critical failure.

### 3. Be specific and actionable
Every finding must include: what's wrong, where it is (file + line), why it matters, and how to fix it. Never say "improve code quality" without pointing to the exact issue.

### 4. Score honestly
A plugin by a trusted org with security issues still gets a security failure. A community plugin with great code still gets credit. Judge the code, not the author.

### 5. Check the real plugin framework
Always verify the plugin under assessment against the actual FiftyOne plugin system. Use MCP tools to list operators, get schemas, and check registration — don't just read files.

```python
list_plugins(enabled=True)
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@org/operator-name")
```

## Evaluation Workflow

### Phase 1: Manifest & Structure

Check the plugin is well-formed before loading it.

**1.1 Parse `fiftyone.yml`:**
- `name` exists and follows convention (`@org/plugin-name`)
- `version` is present and valid semver
- `fiftyone.version` constraint is specified
- `operators` and/or `panels` lists are non-empty
- `secrets` are declared if the plugin uses API keys

**1.2 Skills declaration:**
- Check if `fiftyone.yml` includes a `skills:` section listing companion skills (similar to `operators:` and `panels:`)
- If `skills:` is declared, verify each listed skill has a matching `SKILL.md` file in the plugin directory following the Agent Skills format (YAML frontmatter with `name` and `description`, plus workflow sections)
- If no `skills:` section exists, note this as an observation — the plugin does not ship with companion skills for AI assistants. This is not a penalty, but plugins with skills have higher agent success rates.

**1.3 File structure:**
- `__init__.py` exists
- Every operator in manifest has a matching class in the Python entry file
- Every panel in manifest has a matching class
- If panels declare: `dist/index.umd.js` exists (built JS bundle)
- `requirements.txt` exists if the plugin imports non-standard packages

**1.3 Dependencies:**
- All Python imports resolve (`importlib.util.find_spec`)
- No pinned versions that conflict with FiftyOne's dependencies

**Fail criteria:** Missing `fiftyone.yml`, missing `name`, or entry file doesn't exist → stop eval, report as broken.

### Phase 2: Security & Trust

**This is the most critical phase.** FiftyOne plugins run with full OS-level permissions — no sandbox. A plugin can read files, make network calls, run commands, and access environment variables. Check for misuse.

**2.1 Filesystem access — scan all Python files for:**
```python
# CRITICAL: Look for these patterns
open()           # File read/write — is it within the plugin directory or dataset paths?
os.path          # Path manipulation — is it accessing user home, SSH keys, credentials?
shutil           # File copying — where is it copying to?
pathlib          # Same as os.path
glob.glob        # File discovery — what directories is it scanning?
```

**Acceptable:** Reading/writing within FiftyOne dataset directories, plugin directory, temp files.
**Suspicious:** Reading `~/.ssh/`, `~/.aws/`, `~/.config/`, `/etc/`, or any path outside FiftyOne scope.
**Critical:** Writing to system directories or reading credential files. Plugin properly leverages and handles environment variables 

**2.2 Network access — scan for:**
```python
# CRITICAL: Look for these patterns
requests         # HTTP calls — to where?
urllib           # Same
http.client      # Same
socket           # Raw sockets — almost never legitimate for a plugin
aiohttp          # Async HTTP
httpx            # Same
```

**Acceptable:** Calls to documented APIs and services the plugin integrates with (e.g., annotation backend, model API) that match declared secrets.
**Suspicious:** Calls to unknown external endpoints, IP addresses, or domains not directly related to the plugin's stated purpose or related services.
**Critical:** Data being sent to external servers that includes dataset content, user info, or environment variables.

**2.3 Command execution — scan for:**
```python
# CRITICAL: These should rarely appear in plugins
subprocess       # Shell commands — what commands?
os.system        # Same
os.popen         # Same
exec()           # Dynamic code execution
eval()           # Same
__import__       # Dynamic imports
importlib        # Another pattern for dynamic imports
```

**Acceptable:** Running specific, documented external tools (e.g., `ffmpeg` for video processing in an I/O plugin).
**Suspicious:** Running arbitrary shell commands, especially quietly or in an obfuscated manner, with user-provided input.
**Critical:** `exec()` or `eval()` on any string, bytes, or arbitrary code not directly included in plaintext with the plugin.

**2.4 Environment variable access:**
```python
# Check for broad env var access
os.environ       # Reading ALL env vars — plugins should only use declared secrets
os.getenv        # Reading specific env vars — which ones?
```

**Acceptable:** Reading env vars that match the plugin's declared `secrets` in `fiftyone.yml`.
**Suspicious:** Reading env vars not declared as secrets (e.g., `AWS_SECRET_ACCESS_KEY`, `GITHUB_TOKEN`).
**Critical:** Iterating over `os.environ` to dump all environment variables or sending environment variable contents to locations not related to service authentication.

**2.5 Data exfiltration patterns — check for combinations:**
- Reads a file + makes a network call in the same function → suspicious
- Reads env vars + makes a network call → suspicious
- Accesses dataset samples and/or writes to a non-FiftyOne path → suspicious
- Patterns allowing arbitrary path traversal or relative path access
- Base64 encoding + network call → highly suspicious

**2.6 Dependency supply chain:**
- Check `requirements.txt` for known malicious packages
- Check for typos (e.g., `reqeusts` instead of `requests`)
- Flag packages with very low download counts or no source repository

**Fail criteria:** Any critical finding in 2.1–2.5 → plugin is unsafe, stop eval and report immediately.

### Phase 3: Registration & MCP Readiness

Load the plugin and verify it integrates correctly with FiftyOne.

**3.1 Registration:**
```python
list_plugins(enabled=True)  # Plugin appears?
list_operators()            # All declared operators visible?
```
- `register()` function completes without errors
- All operators from manifest appear in registry
- No name collisions with builtin `@voxel51/*` operators

**3.2 MCP tool exposure: (Optional)** 
- Operators that should be LLM-accessible are exposed as MCP tools
- Internal/helper operators are correctly marked as `unlisted=True`
- Each exposed tool has a description that would help an LLM choose it

**3.3 Startup behavior:**
- If any operator has `on_startup=True`, verify it executes cleanly
- Startup operators should be fast (< 1 second) and side-effect free

### Phase 4: Schema & Contract Quality

Check that every operator has well-defined inputs and outputs.

**4.1 Input schemas:**
```python
# For each public operator
get_operator_schema(operator_uri="@org/operator-name")
```
- `resolve_input()` returns a valid property tree
- Required fields are marked as `required=True`
- Fields have descriptive labels (not "field1", "param_a")
- Enums have reasonable option lists
- Dynamic operators (`dynamic=True`) adapt their schemas correctly

**4.2 Output schemas:**
- `resolve_output()` exists for operators that return meaningful data
- Output types match what `execute()` actually returns

**4.3 Error handling:**
- Empty params → clean validation error, not a crash
- Wrong types → clean error message
- Missing required fields → clear indication of what's missing

### Phase 5: Risk Classification

Check that operators are correctly classified by danger level.

**5.1 Operator severity declaration:**
- Check if operators declare a `severity` in their `OperatorConfig` (e.g., `foo.OperatorConfig(..., severity=foo.Severity.DANGEROUS)`)
- FiftyOne supports severity levels that control how operators are presented and confirmed in the App
- If no `severity` is set on any operator, note this as an observation — the plugin does not use the built-in severity system. This means the App won't show automatic risk indicators or confirmation prompts based on severity.

**5.2 Destructive operations:**
- Any operator that deletes samples, fields, datasets, or files should have `allow_delegated_execution=True` or require confirmation
- Check for: `dataset.delete_samples()`, `dataset.delete_field()`, `sample.delete()`, `shutil.rmtree()`, `os.remove()`
- Destructive operations MUST NOT be auto-executable without user confirmation

**5.2 Data modification:**
- Operators that modify sample fields, add labels, or change metadata should be clearly labeled
- Users must be notified of all expected changes before execution

**5.3 External side effects:**
- Operators that make API calls, send data externally, or trigger external systems should require explicit user consent
- Check if the operator description warns the user about external calls

**5.4 Cost implications:**
- Operators that trigger paid API calls (LLM inference, cloud compute) should document expected cost
- `allow_delegated_execution` should be true for long-running paid operations

### Phase 6: Code Quality

Check the plugin follows FiftyOne conventions.

**6.1 FiftyOne patterns:**
- Uses `ctx.target_view()` for processing (not raw `ctx.dataset`)
- Uses `ctx.store()` with namespaced keys (not generic "data" or "config")
- Delegated execution for operations processing >100 samples
- Generator pattern (`execute_as_generator`) for operations >1 second
- Progress reporting for long operations

**6.2 Code style:**
- Follows `fiftyone-code-style` conventions (imports, naming, aliases)
- No hardcoded dataset names, file paths, or model names
- Dynamic discovery via `list_operators()`, `get_operator_schema()` instead of assumptions

**6.3 ExecutionStore usage:**
- Store keys are scoped (include plugin name and dataset ID)
- TTL set on cached data (not storing forever)
- No reading other plugins' store keys

### Phase 7: Agent Discoverability

Check that an LLM agent can effectively use this plugin's tools.

**7.1 Tool naming:**
- Operator names describe what they do (`compute_embeddings`, not `run_pipeline_v2`)
- Names are distinct from builtin operators (no confusion with `@voxel51/*` tools)

**7.2 Tool descriptions:**
- Each operator's `label` and `description` clearly explain when to use it
- A non-expert reading just the description could decide whether this tool fits their task

**7.3 Ambiguity check:**
- No two operators in the plugin have overlapping descriptions
- The distinction between similar operators is clear (e.g., "import_images" vs "import_labels")

**7.4 Companion skills:**
- Check if the plugin declares `skills:` in `fiftyone.yml` (verified in Phase 1.2)
- If skills exist, verify each skill provides a clear step-by-step workflow that reference the plugin's operators
- If no skills exist and the plugin has >3 operators that are typically used in sequence, recommend creating one — it would improve agent success rate significantly

## Report Format

Generate the report in this structure:

```markdown
# Plugin Eval Report: {plugin_name}

## Summary
- **Overall Score:** {score}/100
- **Security:** {PASS | WARN | FAIL}
- **Quality:** {score}/100
- **Agent Readiness:** {score}/100
- **Critical Issues:** {count}
- **Warnings:** {count}

## Security Assessment
{List each finding with severity, file, line, description, and fix}

## Critical Issues
{Findings that must be fixed before the plugin is safe to use}

## Warnings
{Findings that should be fixed but don't block usage}

## Passed Checks
{What the plugin does well — give credit where due}

## Recommendations
{Ordered list: most impactful fix first, with specific instructions}

## Component Scores
| Area | Score | Key Finding |
|------|-------|-------------|
| Manifest & Structure | {score} | {one-line summary} |
| Security & Trust | {score} | {one-line summary} |
| Registration & MCP | {score} | {one-line summary} |
| Schema & Contract | {score} | {one-line summary} |
| Risk Classification | {score} | {one-line summary} |
| Code Quality | {score} | {one-line summary} |
| Agent Discoverability | {score} | {one-line summary} |
```

## Scoring

**Overall = weighted average:**
- Security & Trust: 30% (safety is non-negotiable)
- Schema & Contract: 20% (correctness matters)
- Agent Discoverability: 15% (usability for LLM agents)
- Risk Classification: 15% (user safety)
- Code Quality: 10% (maintainability)
- Registration & MCP: 5% (basic functionality)
- Manifest & Structure: 5% (basic hygiene)

**Security scoring:**
- 0 critical findings → PASS
- 1+ suspicious findings → WARN (usable with caution)
- 1+ critical findings → FAIL (do not install)

## Quick Reference

### Common Security Patterns to Flag

| Pattern | Severity | Why |
|---------|----------|-----|
| `os.environ` iteration | Critical | Dumps all env vars including secrets |
| `subprocess` + user input | Critical | Command injection risk |
| `exec()` / `eval()` | Critical | Arbitrary code execution |
| `requests.post()` + dataset data | Critical | Data exfiltration |
| `open("/etc/...")` | Critical | System file access |
| `open("~/.ssh/...")` | Critical | Credential theft |
| `socket.connect()` | Suspicious | Raw network access |
| `os.getenv("AWS_*")` undeclared | Suspicious | Accessing secrets not in manifest |
| `shutil.copytree()` to external path | Suspicious | Data copying |
| No `resolve_input()` | Warning | Unvalidated inputs |
| Generic store keys | Warning | Cross-plugin data leaks |

### Score Interpretation

| Score | Meaning |
|-------|---------|
| 90-100 | Production-ready, well-built plugin |
| 70-89 | Good plugin with minor improvements needed |
| 50-69 | Usable but has significant gaps |
| 30-49 | Needs major work before deployment |
| 0-29 | Unsafe or fundamentally broken |

## Troubleshooting

**Plugin won't load for evaluation:**
- Check `fiftyone.yml` exists and has valid YAML syntax
- Check Python entry file has no import errors
- Try: `python -c "import fiftyone; fiftyone.plugins.list_plugins()"`

**Can't check MCP exposure:**
- Verify FiftyOne MCP server is available
- Check: `fiftyone-mcp` binary exists in PATH

**Security scan finds too many false positives:**
- Check if flagged patterns are inside test files (tests/ directory) — lower severity
- Check if network calls match declared secrets — likely legitimate
- Use context: an I/O plugin making HTTP calls to a documented API is expected

## Resources

- [FiftyOne Plugin Development Guide](https://docs.voxel51.com/plugins/developing_plugins.html)
- [Anthropic's Framework for Safe Agents](https://www.anthropic.com/news/our-framework-for-developing-safe-and-trustworthy-agents)
- [FiftyOne Plugins Repository](https://github.com/voxel51/fiftyone-plugins)
- [fiftyone-develop-plugin skill](../fiftyone-develop-plugin/SKILL.md) — for fixing code quality issues
- [fiftyone-code-style skill](../fiftyone-code-style/SKILL.md) — for fixing style issues
