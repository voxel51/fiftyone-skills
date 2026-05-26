"""FiftyOne Skills installer CLI."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import sys
import sysconfig
import urllib.request
from pathlib import Path


__version__ = "0.1.0"

logger = logging.getLogger(__name__)

AGENT_DIRS = {
    "claude": ".claude/skills",
    "codex": ".codex/skills",
    "cursor": ".cursor/skills",
    "copilot": ".github/copilot/skills",
}

CLI_DESCRIPTION = "Install FiftyOne Skills for AI assistants"
CLI_EXAMPLES = """
Examples:
  # Install locally for Claude Code
  fiftyone-skills env=local agent=claude

  # Install globally for Cursor
  fiftyone-skills env=global agent=cursor

  # Install locally to .agents/skills/ directory
  fiftyone-skills env=local agent=None

  # Update skills from GitHub
  fiftyone-skills env=local agent=claude --update
"""


def _setup_logging() -> None:
    """Configure logging for CLI output: INFO to stdout, WARNING+ to stderr."""
    fmt = logging.Formatter("%(message)s")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(fmt)
    stdout_handler.addFilter(lambda rec: rec.levelno < logging.WARNING)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(stdout_handler)
    root.addHandler(stderr_handler)


def get_package_skills_dir() -> Path:
    """Get the skills directory from the installed package."""
    # Check the wheel data install location (sysconfig 'data' scheme)
    data_skills = Path(sysconfig.get_path("data")) / "skills"
    if data_skills.exists():
        return data_skills

    # Fallback for development/editable installs: walk up from the module
    module_dir = Path(__file__).parent
    for parent in module_dir.parents:
        skills_dir = parent / "skills"
        if skills_dir.is_dir() and any(
            d.is_dir() and d.name.startswith("fiftyone-") for d in skills_dir.iterdir()
        ):
            return skills_dir

    raise FileNotFoundError(
        "Could not find skills directory. "
        "Please ensure fiftyone-skills is properly installed."
    )


def get_install_dir(env: str, agent: str | None = None) -> Path:
    """Determine the installation directory based on env and agent."""
    if env == "local":
        base_dir = Path.cwd()
    elif env == "global":
        base_dir = Path.home()
    else:
        raise ValueError(f"Invalid env value: {env}. Must be 'local' or 'global'")

    if agent and (agent_key := agent.lower()) != "none":
        if agent_key not in AGENT_DIRS:
            raise ValueError(
                f"Invalid agent: {agent}. "
                f"Must be one of: {', '.join(AGENT_DIRS.keys())}, None"
            )
        return base_dir / AGENT_DIRS[agent_key]

    return base_dir / ".agents" / "skills"


def copy_skills(src_dir: Path, dest_dir: Path) -> int:
    """Copy skills from source to destination directory."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    skill_count = 0
    for skill_path in src_dir.iterdir():
        if skill_path.is_dir() and not skill_path.name.startswith("."):
            dest_path = dest_dir / skill_path.name

            if dest_path.exists():
                shutil.rmtree(dest_path)

            shutil.copytree(skill_path, dest_path)
            skill_count += 1
            logger.info("  ✓ %s", skill_path.name)

    return skill_count


def _git_blob_sha(path: Path) -> str:
    """Compute the git blob SHA1 for a local file."""
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def _fetch_json(url: str) -> list[dict]:
    """Fetch JSON from a URL using urllib."""
    req = urllib.request.Request(url, headers={"User-Agent": "fiftyone-skills-cli"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _sync_directory(
    api_base: str, remote_path: str, local_dir: Path, branch: str
) -> tuple[int, int]:
    """Recursively sync a remote GitHub directory to a local directory.

    Returns (files_downloaded, files_skipped).
    """
    entries = _fetch_json(f"{api_base}/{remote_path}?ref={branch}")
    local_dir.mkdir(parents=True, exist_ok=True)

    downloaded = skipped = 0
    for entry in entries:
        if entry["type"] == "file":
            dest = local_dir / entry["name"]
            if dest.exists() and _git_blob_sha(dest) == entry["sha"]:
                skipped += 1
                continue
            req = urllib.request.Request(
                entry["download_url"], headers={"User-Agent": "fiftyone-skills-cli"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                dest.write_bytes(resp.read())
            downloaded += 1
        elif entry["type"] == "dir":
            d, s = _sync_directory(
                api_base, entry["path"], local_dir / entry["name"], branch
            )
            downloaded += d
            skipped += s

    return downloaded, skipped


def download_skills_from_github(
    dest_dir: Path, repo: str = "voxel51/fiftyone-skills", branch: str = "main"
) -> None:
    """Download/update skills from GitHub using the Contents API."""
    api_base = f"https://api.github.com/repos/{repo}/contents"

    logger.info("Fetching skills from %s@%s...", repo, branch)

    try:
        entries = _fetch_json(f"{api_base}/skills?ref={branch}")
    except Exception as e:
        logger.error("Error fetching skills list from GitHub: %s", e)
        logger.error(
            "Please check your internet connection and that the repository is accessible."
        )
        sys.exit(1)

    skill_dirs = [
        e for e in entries if e["type"] == "dir" and not e["name"].startswith(".")
    ]

    logger.info("\nUpdating skills:")
    total_dl = total_skip = 0
    for skill in skill_dirs:
        try:
            dl, skip = _sync_directory(
                api_base, skill["path"], dest_dir / skill["name"], branch
            )
            total_dl += dl
            total_skip += skip
            status = f"{dl} file(s) updated" if dl else "up to date"
            logger.info("  ✓ %s (%s)", skill["name"], status)
        except Exception as e:
            logger.warning("  ✗ %s: %s", skill["name"], e)

    logger.info(
        "\n✓ %d skills processed: %d file(s) updated, %d unchanged",
        len(skill_dirs),
        total_dl,
        total_skip,
    )


def install_skills(env: str, agent: str | None = None, update: bool = False) -> None:
    """Install FiftyOne skills to the specified location."""
    install_dir = get_install_dir(env, agent)

    if update:
        download_skills_from_github(install_dir)
    else:
        try:
            skills_dir = get_package_skills_dir()
        except FileNotFoundError as e:
            logger.error("Error: %s", e)
            sys.exit(1)

        logger.info("\nInstalling skills to %s:", install_dir)
        skill_count = copy_skills(skills_dir, install_dir)
        logger.info(
            "\n✓ Successfully installed %d skills to %s", skill_count, install_dir
        )

    sep = "=" * 60
    logger.info("\n%s\nInstallation complete!\n%s", sep, sep)

    if agent and agent.lower() != "none":
        logger.info("\nSkills installed for %s agent at:", agent.upper())
    else:
        logger.info("\nSkills installed at:")
    logger.info("  %s", install_dir)

    logger.info("\nTo use these skills, configure your AI assistant to load them.")
    logger.info("Refer to the README.md for agent-specific setup instructions.")


def main() -> None:
    """Main entry point for the CLI."""
    _setup_logging()

    parser = argparse.ArgumentParser(
        description=CLI_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=CLI_EXAMPLES,
    )

    parser.add_argument(
        "config",
        nargs="*",
        help="Configuration in format key=value (e.g., env=local agent=claude)",
    )

    parser.add_argument(
        "--update",
        action="store_true",
        help="Update skills by downloading from GitHub repository",
    )

    parser.add_argument(
        "--version", action="version", version=f"fiftyone-skills {__version__}"
    )

    args = parser.parse_args()

    # Parse key=value arguments
    config = {}
    valid_keys = ("env", "agent")

    for item in args.config:
        if "=" in item:
            key, value = item.split("=", 1)
            if key not in valid_keys:
                logger.error("Error: Unknown argument '%s'", key)
                logger.error("Valid arguments are: %s", ", ".join(valid_keys))
                sys.exit(1)
            config[key] = value
        else:
            logger.error("Error: Invalid argument format: %s", item)
            logger.error("Arguments must be in format key=value")
            sys.exit(1)

    # Validate required arguments
    if "env" not in config:
        logger.error("Error: 'env' argument is required (env=local or env=global)")
        parser.print_help()
        sys.exit(1)

    env = config["env"]
    agent = config.get("agent")

    try:
        install_skills(env, agent, update=args.update)
    except Exception as e:
        logger.error("Error: %s", e)
        sys.exit(1)
