# Installation Guide

This guide covers how to install and use the `fiftyone-skills` Python package.

## Prerequisites

- Python 3.8 or higher
- pip or uv package manager

## Installation Methods

### Option 1: Install from PyPI (Recommended)

Once published to PyPI, you can install with:

```bash
pip install fiftyone-skills
```

### Option 2: Install from Source

Clone the repository and install:

```bash
git clone https://github.com/voxel51/fiftyone-skills.git
cd fiftyone-skills
pip install -e .
```

Or using `uv`:

```bash
git clone https://github.com/voxel51/fiftyone-skills.git
cd fiftyone-skills
uv pip install -e .
```

### Option 3: Build and Install Wheel

```bash
git clone https://github.com/voxel51/fiftyone-skills.git
cd fiftyone-skills
uv build
pip install dist/fiftyone_skills-*.whl
```

## Usage

After installation, the `fiftyone-skills` command will be available in your terminal.

### Basic Syntax

```bash
fiftyone-skills env=<local|global> agent=<agent-name> [--update]
```

### Arguments

- **env** (required): Installation scope
  - `local` - Install to current project directory
  - `global` - Install to user's home directory

- **agent** (required): Target AI assistant
  - `claude` - Claude Code/Desktop (installs to `.claude/skills/`)
  - `cursor` - Cursor editor (installs to `.cursor/skills/`)
  - `codex` - GitHub Codex (installs to `.codex/skills/`)
  - `copilot` - GitHub Copilot (installs to `.github/copilot/skills/`)
  - `None` - Generic location (installs to `.agents/skills/`)

- **--update** (optional): Download latest skills from GitHub instead of using packaged version

### Examples

#### Install locally for Claude Code

```bash
fiftyone-skills env=local agent=claude
```

This installs skills to `<current-directory>/.claude/skills/`

#### Install globally for Cursor

```bash
fiftyone-skills env=global agent=cursor
```

This installs skills to `~/.cursor/skills/`

#### Install locally to generic location

```bash
fiftyone-skills env=local agent=None
```

This installs skills to `<current-directory>/.agents/skills/`

#### Update skills from GitHub

```bash
fiftyone-skills env=local agent=claude --update
```

This downloads the latest skills from the GitHub repository and installs them.

## Installation Locations

### Local Installation (env=local)

Skills are installed relative to your current working directory:

- `claude`: `./.claude/skills/`
- `cursor`: `./.cursor/skills/`
- `codex`: `./.codex/skills/`
- `copilot`: `./.github/copilot/skills/`
- `None`: `./.agents/skills/`

### Global Installation (env=global)

Skills are installed in your home directory:

- `claude`: `~/.claude/skills/`
- `cursor`: `~/.cursor/skills/`
- `codex`: `~/.codex/skills/`
- `copilot`: `~/.github/copilot/skills/`
- `None`: `~/.agents/skills/`

## Cross-Platform Support

The package works on:
- **macOS** - Full support
- **Linux** - Full support
- **Windows** - Full support (uses Windows path separators automatically)

## What Gets Installed

The installer copies all skill directories to your chosen location:

- `fiftyone-dataset-import/` - Dataset import workflows
- `fiftyone-dataset-export/` - Dataset export workflows
- `fiftyone-find-duplicates/` - Duplicate detection
- `fiftyone-dataset-inference/` - Model inference
- `fiftyone-model-evaluation/` - Model evaluation
- `fiftyone-embeddings-visualization/` - Embeddings visualization
- `fiftyone-develop-plugin/` - Plugin development
- `fiftyone-code-style/` - FiftyOne code style guide
- `fiftyone-voodo-design/` - VOODO UI design system
- `fiftyone-issue-triage/` - GitHub issue triage
- `fiftyone-create-notebook/` - Jupyter notebook creation

Each skill directory contains:
- `SKILL.md` - Main skill documentation and instructions
- Additional reference files (varies by skill)

## Verifying Installation

After installation, verify the skills were copied:

```bash
# For local Claude installation
ls -la .claude/skills/

# For global Cursor installation
ls -la ~/.cursor/skills/
```

You should see all skill directories listed.

## Updating Skills

To get the latest skills from GitHub:

```bash
fiftyone-skills env=local agent=claude --update
```

This will:
1. Download the latest `main` branch from GitHub
2. Extract all skills
3. Install them to your specified location
4. Overwrite any existing skills

## Troubleshooting

### Command not found

If `fiftyone-skills` command is not found after installation:

1. Ensure the installation directory is in your PATH
2. Try using the full path: `python -m fiftyone_skills`
3. Restart your terminal

### Permission errors on global install

On some systems, you may need to use `--user` flag:

```bash
pip install --user fiftyone-skills
```

### Network errors with --update

The `--update` flag requires internet access to download from GitHub. If you're behind a proxy or firewall, the download may fail. In that case, use the packaged version (without `--update`).

## Uninstalling

To uninstall the package:

```bash
pip uninstall fiftyone-skills
```

Note: This only removes the Python package. Installed skills in `.claude/skills/`, etc. remain on disk. Remove them manually if desired:

```bash
# Remove local skills
rm -rf .claude/skills/
rm -rf .cursor/skills/
# etc.

# Remove global skills
rm -rf ~/.claude/skills/
rm -rf ~/.cursor/skills/
# etc.
```

## Next Steps

After installation:

1. Configure your AI assistant to use the skills (see README.md)
2. Try the skills with natural language commands
3. Refer to individual skill documentation in each `SKILL.md` file

## Support

- [Documentation](https://docs.voxel51.com)
- [GitHub Issues](https://github.com/voxel51/fiftyone-skills/issues)
- [Discord Community](https://discord.gg/fiftyone-community)
