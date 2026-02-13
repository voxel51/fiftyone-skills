"""FiftyOne Skills installer CLI."""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Optional


__version__ = "0.1.0"


# Agent-specific directory mappings
AGENT_DIRS = {
    "claude": ".claude/skills",
    "codex": ".codex/skills", 
    "cursor": ".cursor/skills",
    "copilot": ".github/copilot/skills",
}


def get_package_skills_dir() -> Path:
    """Get the skills directory from the installed package."""
    # Try to find skills directory relative to this module
    module_dir = Path(__file__).parent
    
    # Check if skills is in the package
    if (module_dir / "skills").exists():
        return module_dir / "skills"
    
    # Check parent directories (for development/editable install)
    for parent in module_dir.parents:
        skills_dir = parent / "skills"
        if skills_dir.exists() and (skills_dir / "fiftyone-find-duplicates").exists():
            return skills_dir
    
    raise FileNotFoundError(
        "Could not find skills directory. "
        "Please ensure fiftyone-skills is properly installed."
    )


def get_install_dir(env: str, agent: Optional[str] = None) -> Path:
    """Determine the installation directory based on env and agent."""
    if env == "local":
        # Project-local installation
        base_dir = Path.cwd()
    elif env == "global":
        # User-global installation
        base_dir = Path.home()
    else:
        raise ValueError(f"Invalid env value: {env}. Must be 'local' or 'global'")
    
    if agent and agent.lower() != "none":
        # Install to agent-specific directory
        agent_key = agent.lower()
        if agent_key not in AGENT_DIRS:
            raise ValueError(
                f"Invalid agent: {agent}. "
                f"Must be one of: {', '.join(AGENT_DIRS.keys())}, None"
            )
        return base_dir / AGENT_DIRS[agent_key]
    else:
        # Install to .agents/skills/ directory
        return base_dir / ".agents" / "skills"


def copy_skills(src_dir: Path, dest_dir: Path) -> None:
    """Copy skills from source to destination directory."""
    # Create destination directory if it doesn't exist
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy each skill directory
    skill_count = 0
    for skill_path in src_dir.iterdir():
        if skill_path.is_dir() and not skill_path.name.startswith('.'):
            dest_path = dest_dir / skill_path.name
            
            # Remove existing if present
            if dest_path.exists():
                shutil.rmtree(dest_path)
            
            # Copy the skill directory
            shutil.copytree(skill_path, dest_path)
            skill_count += 1
            print(f"  ✓ {skill_path.name}")
    
    return skill_count


def download_skills_from_github(dest_dir: Path, repo: str = "voxel51/fiftyone-skills", branch: str = "main") -> None:
    """Download skills from GitHub repository."""
    import urllib.request
    import json
    import tempfile
    import zipfile
    import os
    
    print(f"Downloading skills from {repo}@{branch}...")
    
    # Download the repository as a zip file
    zip_url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        zip_path = tmpdir_path / "repo.zip"
        
        # Download zip file
        try:
            urllib.request.urlretrieve(zip_url, zip_path)
        except Exception as e:
            print(f"Error downloading from GitHub: {e}", file=sys.stderr)
            print("Please check your internet connection and that the repository is accessible.", file=sys.stderr)
            sys.exit(1)
        
        # Extract zip file with path validation
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Validate all paths before extraction to prevent path traversal attacks
            for member in zip_ref.namelist():
                # Normalize the path and ensure it doesn't escape the temp directory
                member_path = (tmpdir_path / member).resolve()
                if not str(member_path).startswith(str(tmpdir_path.resolve())):
                    print(f"Error: Malicious path detected in zip file: {member}", file=sys.stderr)
                    sys.exit(1)
            
            # Safe to extract after validation
            zip_ref.extractall(tmpdir_path)
        
        # Find the extracted directory (it will be named repo-branch)
        repo_name = repo.split('/')[-1]
        extracted_dir = tmpdir_path / f"{repo_name}-{branch}"
        
        if not extracted_dir.exists():
            print(f"Error: Could not find extracted directory at {extracted_dir}", file=sys.stderr)
            sys.exit(1)
        
        # Copy skills from extracted directory
        skills_src = extracted_dir / "skills"
        if not skills_src.exists():
            print(f"Error: No skills directory found in {repo}", file=sys.stderr)
            sys.exit(1)
        
        print("\nInstalling skills:")
        skill_count = copy_skills(skills_src, dest_dir)
        print(f"\n✓ Successfully installed {skill_count} skills to {dest_dir}")


def install_skills(env: str, agent: Optional[str] = None, update: bool = False) -> None:
    """Install FiftyOne skills to the specified location."""
    # Determine installation directory
    install_dir = get_install_dir(env, agent)
    
    if update:
        # Download latest from GitHub
        download_skills_from_github(install_dir)
    else:
        # Install from package
        try:
            skills_dir = get_package_skills_dir()
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        
        print(f"\nInstalling skills from package to {install_dir}...")
        print("\nInstalling skills:")
        skill_count = copy_skills(skills_dir, install_dir)
        print(f"\n✓ Successfully installed {skill_count} skills to {install_dir}")
    
    # Print usage information
    print("\n" + "=" * 60)
    print("Installation complete!")
    print("=" * 60)
    
    if agent and agent.lower() != "none":
        print(f"\nSkills installed for {agent.upper()} agent at:")
    else:
        print("\nSkills installed at:")
    print(f"  {install_dir}")
    
    print("\nTo use these skills, configure your AI assistant to load them.")
    print("Refer to the README.md for agent-specific setup instructions.")


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Install FiftyOne Skills for AI assistants",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
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
    )
    
    parser.add_argument(
        "config",
        nargs="*",
        help="Configuration in format key=value (e.g., env=local agent=claude)"
    )
    
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update skills by downloading from GitHub repository"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"fiftyone-skills {__version__}"
    )
    
    args = parser.parse_args()
    
    # Parse key=value arguments
    config = {}
    valid_keys = {"env", "agent"}
    
    for item in args.config:
        if "=" in item:
            key, value = item.split("=", 1)
            if key not in valid_keys:
                print(f"Error: Unknown argument '{key}'", file=sys.stderr)
                print(f"Valid arguments are: {', '.join(valid_keys)}", file=sys.stderr)
                sys.exit(1)
            config[key] = value
        else:
            print(f"Error: Invalid argument format: {item}", file=sys.stderr)
            print("Arguments must be in format key=value", file=sys.stderr)
            sys.exit(1)
    
    # Validate required arguments
    if "env" not in config:
        print("Error: 'env' argument is required (env=local or env=global)", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    env = config["env"]
    agent = config.get("agent")
    
    # Validate env value
    if env not in ["local", "global"]:
        print(f"Error: env must be 'local' or 'global', got '{env}'", file=sys.stderr)
        sys.exit(1)
    
    # Validate agent value
    if agent and agent.lower() not in list(AGENT_DIRS.keys()) + ["none"]:
        print(
            f"Error: agent must be one of: {', '.join(AGENT_DIRS.keys())}, None; got '{agent}'",
            file=sys.stderr
        )
        sys.exit(1)
    
    try:
        install_skills(env, agent, update=args.update)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
