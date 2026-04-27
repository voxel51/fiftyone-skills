# Contributing to FiftyOne Skills

Thank you for your interest in contributing! FiftyOne Skills are packaged workflows that teach AI assistants to perform complex computer vision tasks, and the community is what makes them better.

> **New here?** Browse [open issues](https://github.com/voxel51/fiftyone-skills/issues?q=is%3Aopen+label%3A%22help+wanted%22) labeled `help wanted` or `good first issue` to find a great starting point.

## Ways to Contribute

There are two main ways to contribute:

- **New skill** — Teach an AI assistant a workflow it doesn't know yet
- **Improve an existing skill** — Fix a bug, improve accuracy, add edge cases, or add supporting reference docs

Both follow the same workflow below.

## Before You Start

1. **Check existing skills** — Browse [`skills/`](skills/) to make sure there isn't already a skill that covers your use case
2. **Check open issues** — Someone may already be working on it, or there may be useful context in an existing issue
3. **Look at the roadmap** — See [GitHub Milestones](https://github.com/voxel51/fiftyone-skills/milestones) and issues labeled [`roadmap`](https://github.com/voxel51/fiftyone-skills/labels/roadmap) for planned work

No permission needed to start contributing — just submit your PR when it's ready.

## Contribution Workflow

### 1. Fork and clone

```bash
git clone https://github.com/<your-username>/fiftyone-skills.git
cd fiftyone-skills
```

### 2. Create a branch

```bash
git checkout -b feat/fiftyone-my-skill
```

Branch naming: `feat/<skill-name>` for new skills, `fix/<skill-name>` for improvements.

### 3. Copy the closest existing skill as a starting point

```bash
cp -r skills/fiftyone-find-duplicates skills/fiftyone-my-skill
```

For simple skills, `fiftyone-find-duplicates` is a good template.  
For MCP-heavy skills, use `fiftyone-dataset-import`.  
For plugin development, use `fiftyone-develop-plugin`.

### 4. Write your `SKILL.md`

See the [Skill Structure](#skill-structure) section below for the required format.

### 5. Test with your AI assistant

Load the skill and run through your workflow end-to-end. The skill should guide the agent correctly without manual correction.

**Claude Code:**
```bash
/plugin install fiftyone-my-skill@fiftyone-skills
```

### 6. Validate the template

```bash
node scripts/validate-template.mjs
```

This checks frontmatter, path safety, and naming conventions. Fix any errors before submitting.

### 7. Update `AGENTS.md`

Add an entry for your skill under the **Available Skills** section of `AGENTS.md`. Follow the existing format:

```markdown
### FiftyOne My Skill (`fiftyone-my-skill/`)

**When to use:** [One sentence describing when an agent should load this skill]

**Instructions:** Load the skill file at `skills/fiftyone-my-skill/SKILL.md`

**Key requirements:**
- [Any dependencies, plugins, or MCP tools required]

**Workflow summary:**
1. Step one
2. Step two
3. ...
```

### 8. Submit a Pull Request

Push your branch and open a PR against `main`. The PR template will guide you through the checklist.

## Skill Structure

Each skill lives in its own directory under `skills/`:

```
skills/
└── fiftyone-my-skill/
    ├── SKILL.md              # Required — instructions for the AI
    ├── references/           # Optional — supporting reference docs
    │   └── SOME-GUIDE.md
    └── scripts/              # Optional — example or utility scripts
        └── example.py
```

### `SKILL.md` format

Every `SKILL.md` must start with YAML frontmatter:

```markdown
---
name: fiftyone-my-skill
description: One to two sentences describing when to use this skill and what it does.
---
```

The `description` field is what triggers skill activation — write it to match how a user would naturally phrase the task.

### Required sections

| Section | Purpose |
|---------|---------|
| **Key Directives** | `ALWAYS`/`NEVER` rules the agent must follow |
| **Complete Workflow** | Step-by-step instructions with code examples |
| **Troubleshooting** | Common errors, their causes, and fixes |

### Recommended sections

| Section | Purpose |
|---------|---------|
| Available Tools | Table of MCP tools or operators used |
| Common Use Cases | 2–3 real-world examples |
| Best Practices | Tips for reliable results |
| Resources | Links to docs, plugins, or related skills |

### Quality bar

Before submitting, verify your skill:

- [ ] Frontmatter has `name` and `description`
- [ ] `description` triggers on realistic user prompts (not too broad, not too narrow)
- [ ] Key Directives covers the most important rules (5–8 items)
- [ ] Workflow has code examples at each step
- [ ] Troubleshooting covers the most common failure modes
- [ ] Tested end-to-end with at least one AI assistant
- [ ] No inclusion of device-specific references or local-only file pointers

## Naming Conventions

- Skill directories: `fiftyone-<name>` (kebab-case, lowercase)
- Supporting docs: `UPPER-CASE.md` (e.g., `HF-HUB-IMPORT.md`, `FIELD-MAPPING.md`)
- Scripts: `snake_case.py` or `kebab-case.mjs`

## Supported AI Assistants

Skills in this repo are tested against:

| Assistant | Install method |
|-----------|---------------|
| Claude Code | `/plugin install` |
| Cursor | `.cursor-plugin/` |
| Gemini CLI | `gemini extensions install` |
| Codex, Goose, Amp, and more | Universal installer |

If your skill works with a specific assistant only, note it in the `SKILL.md` prerequisites.

## Community

- **Discord**: [FiftyOne Community](https://discord.gg/fiftyone-community) — get help, share your work, discuss ideas
- **Issues**: [GitHub Issues](https://github.com/voxel51/fiftyone-skills/issues) — bugs, feature requests, proposals
- **Feedback**: Ask your AI assistant `"Help me submit feedback about [issue]"` to auto-generate a report

<div align="center">

Copyright 2017–2026, Voxel51, Inc. · [Apache 2.0 License](LICENSE)

</div>
