#!/usr/bin/env python3
"""Generate the Available Skills section of AGENTS.md from SKILL.md frontmatter.

Every ``SKILL.md`` under ``skills/`` is discovered recursively, its YAML
frontmatter is validated, and the section of ``AGENTS.md`` between the
generated-section markers is rewritten. Everything outside the markers is
left untouched, so the rest of the file stays hand-written.

Usage::

    python scripts/generate_agents.py          # rewrite AGENTS.md
    python scripts/generate_agents.py --check  # exit 1 if AGENTS.md is stale

Requires PyYAML (``pip install pyyaml``).
"""

import argparse
import difflib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

BEGIN_MARKER = "<!-- BEGIN GENERATED SKILLS: do not edit, run `python scripts/generate_agents.py` -->"
END_MARKER = "<!-- END GENERATED SKILLS -->"

# Top-level frontmatter keys defined by the Agent Skills spec
# (https://agentskills.io/specification). Anything else is not portable
# across agents.
ALLOWED_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
REQUIRED_KEYS = ("name", "description")

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500

# Words that don't title-case cleanly when building a display title
TITLE_WORDS = {
    "fiftyone": "FiftyOne",
    "sdk": "SDK",
    "voodo": "VOODO",
}


class SkillError(Exception):
    """Raised when one or more SKILL.md files are invalid."""

    def __init__(self, errors):
        super().__init__("\n".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    compatibility: str
    path: Path  # SKILL.md path, relative to the repo root

    @property
    def title(self):
        return " ".join(
            TITLE_WORDS.get(word, word.capitalize())
            for word in self.name.split("-")
        )

    @property
    def directory(self):
        return self.path.parent.relative_to("skills").as_posix() + "/"


def find_skill_files(skills_dir):
    """Returns every SKILL.md under ``skills_dir``, sorted by path."""
    return sorted(p for p in skills_dir.rglob("SKILL.md") if p.is_file())


def parse_frontmatter(text):
    """Returns the frontmatter of ``text`` as a dict.

    Raises:
        ValueError: if the frontmatter is missing or is not a YAML mapping
    """
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter (file must start with '---')")

    end = text.find("\n---\n", 3)
    if end == -1 and text.endswith("\n---"):
        end = len(text) - 4
    if end == -1:
        raise ValueError("frontmatter is not closed with '---'")

    try:
        data = yaml.safe_load(text[4 : end + 1])
    except yaml.YAMLError as e:
        raise ValueError("invalid YAML in frontmatter: %s" % e)

    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a YAML mapping")

    return data


def _validate(data, skill_path):
    errors = []

    for key in REQUIRED_KEYS:
        value = data.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append("missing required field '%s'" % key)
        elif not isinstance(value, str):
            errors.append("'%s' must be a string" % key)

    unknown = sorted(str(k) for k in data if k not in ALLOWED_KEYS)
    if unknown:
        errors.append(
            "unsupported field(s) %s; allowed fields are %s"
            % (", ".join(unknown), ", ".join(sorted(ALLOWED_KEYS)))
        )

    name = data.get("name")
    if isinstance(name, str) and name.strip():
        if len(name) > MAX_NAME_LENGTH or not NAME_PATTERN.match(name):
            errors.append(
                "invalid name '%s': use lowercase letters, digits and single "
                "hyphens, at most %d characters" % (name, MAX_NAME_LENGTH)
            )
        if name != skill_path.parent.name:
            errors.append(
                "name '%s' does not match its directory '%s'"
                % (name, skill_path.parent.name)
            )

    description = data.get("description")
    if isinstance(description, str) and len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            "description is %d characters; the limit is %d"
            % (len(description), MAX_DESCRIPTION_LENGTH)
        )

    compatibility = data.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str):
            errors.append("'compatibility' must be a string")
        elif len(compatibility) > MAX_COMPATIBILITY_LENGTH:
            errors.append(
                "compatibility is %d characters; the limit is %d"
                % (len(compatibility), MAX_COMPATIBILITY_LENGTH)
            )

    return errors


def _one_line(value):
    return " ".join(value.split())


def load_skills(repo_root):
    """Loads and validates every skill under ``repo_root/skills``.

    Returns:
        a list of :class:`Skill`, sorted by name

    Raises:
        SkillError: listing every problem found across all skills
    """
    skills_dir = repo_root / "skills"
    if not skills_dir.is_dir():
        raise SkillError(["skills directory not found: %s" % skills_dir])

    skills = []
    errors = []
    seen = {}

    for skill_file in find_skill_files(skills_dir):
        rel_path = skill_file.relative_to(repo_root)
        try:
            data = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        except ValueError as e:
            errors.append("%s: %s" % (rel_path.as_posix(), e))
            continue

        problems = _validate(data, rel_path)
        if problems:
            errors.extend("%s: %s" % (rel_path.as_posix(), p) for p in problems)
            continue

        name = data["name"]
        if name in seen:
            errors.append(
                "%s: duplicate skill name '%s' (also used by %s)"
                % (rel_path.as_posix(), name, seen[name].as_posix())
            )
            continue
        seen[name] = rel_path

        skills.append(
            Skill(
                name=name,
                description=_one_line(data["description"]),
                compatibility=_one_line(data.get("compatibility") or ""),
                path=rel_path,
            )
        )

    if errors:
        raise SkillError(errors)

    if not skills:
        raise SkillError(["no SKILL.md files found under %s" % skills_dir])

    return sorted(skills, key=lambda s: s.name)


def render_skills(skills):
    """Renders the generated section, including its markers."""
    lines = [BEGIN_MARKER, ""]
    for skill in skills:
        lines.append("### %s (`%s`)" % (skill.title, skill.directory))
        lines.append("")
        lines.append(skill.description)
        lines.append("")
        if skill.compatibility:
            lines.append("**Compatibility:** %s" % skill.compatibility)
            lines.append("")
        lines.append(
            "**Instructions:** Load the skill file at `%s`"
            % skill.path.as_posix()
        )
        lines.append("")
    lines.append(END_MARKER)
    return "\n".join(lines)


def update_agents_md(current, skills):
    """Returns ``current`` with its generated section replaced.

    Raises:
        SkillError: if the markers are missing or out of order
    """
    begin = current.find(BEGIN_MARKER)
    end = current.find(END_MARKER)
    if begin == -1 or end == -1 or end < begin:
        raise SkillError(
            [
                "AGENTS.md must contain the markers\n  %s\n  %s\n"
                "in that order, around the Available Skills entries"
                % (BEGIN_MARKER, END_MARKER)
            ]
        )

    return (
        current[:begin]
        + render_skills(skills)
        + current[end + len(END_MARKER) :]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate AGENTS.md from SKILL.md frontmatter."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="don't write; exit 1 if AGENTS.md is out of date",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="repository root (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    agents_path = args.root / "AGENTS.md"

    try:
        skills = load_skills(args.root)
        current = agents_path.read_text(encoding="utf-8")
        expected = update_agents_md(current, skills)
    except SkillError as e:
        print("AGENTS.md generation failed:", file=sys.stderr)
        for error in e.errors:
            print("- %s" % error, file=sys.stderr)
        return 1

    if current == expected:
        print("AGENTS.md is up to date (%d skills)." % len(skills))
        return 0

    if args.check:
        diff = difflib.unified_diff(
            current.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            fromfile="AGENTS.md",
            tofile="AGENTS.md (expected)",
        )
        sys.stderr.writelines(diff)
        print(
            "\nAGENTS.md is out of date. Run `python scripts/generate_agents.py`"
            " and commit the result.",
            file=sys.stderr,
        )
        return 1

    with open(agents_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(expected)
    print("Wrote AGENTS.md (%d skills)." % len(skills))
    return 0


if __name__ == "__main__":
    sys.exit(main())
