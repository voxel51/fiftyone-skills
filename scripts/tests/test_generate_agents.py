"""Tests for scripts/generate_agents.py.

Run with::

    python -m unittest discover -s scripts/tests
"""

import contextlib
import io
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import generate_agents as ga  # noqa: E402

AGENTS_TEMPLATE = (
    "# Agent Instructions\n\n## Available Skills\n\n"
    + ga.BEGIN_MARKER
    + "\n"
    + ga.END_MARKER
    + "\n\n## Prerequisites\n\nHand-written text.\n"
)


class RepoTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "skills").mkdir()
        (self.root / "AGENTS.md").write_text(AGENTS_TEMPLATE, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def add_skill(self, dirname, frontmatter, body="# Skill\n"):
        skill_dir = self.root / "skills" / dirname
        skill_dir.mkdir(parents=True)
        path = skill_dir / "SKILL.md"
        path.write_text(
            "---\n" + textwrap.dedent(frontmatter).strip() + "\n---\n\n" + body,
            encoding="utf-8",
        )
        return path

    def add_valid_skill(self, dirname, description="Does a thing."):
        name = Path(dirname).name
        return self.add_skill(
            dirname, "name: %s\ndescription: %s" % (name, description)
        )

    def assert_skill_error(self, *fragments):
        with self.assertRaises(ga.SkillError) as ctx:
            ga.load_skills(self.root)
        message = str(ctx.exception)
        for fragment in fragments:
            self.assertIn(fragment, message)
        return ctx.exception

    def run_main(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = ga.main(["--root", str(self.root), *args])
        return code, stdout.getvalue(), stderr.getvalue()

    def agents_md(self):
        return (self.root / "AGENTS.md").read_text(encoding="utf-8")


class LoadSkillsTest(RepoTestCase):
    def test_loads_valid_skills_sorted_by_name(self):
        self.add_valid_skill("fiftyone-zeta")
        self.add_valid_skill("fiftyone-alpha")

        skills = ga.load_skills(self.root)

        self.assertEqual(
            [s.name for s in skills], ["fiftyone-alpha", "fiftyone-zeta"]
        )

    def test_finds_nested_skills(self):
        self.add_valid_skill("group/fiftyone-nested")

        (skill,) = ga.load_skills(self.root)

        self.assertEqual(
            skill.path.as_posix(), "skills/group/fiftyone-nested/SKILL.md"
        )
        self.assertEqual(skill.directory, "group/fiftyone-nested/")

    def test_folded_description_is_joined_into_one_line(self):
        self.add_skill(
            "fiftyone-folded",
            """
            name: fiftyone-folded
            description: >
              First line
              second line.
            """,
        )

        (skill,) = ga.load_skills(self.root)

        self.assertEqual(skill.description, "First line second line.")

    def test_no_skills(self):
        self.assert_skill_error("no SKILL.md files found")


class InvalidMetadataTest(RepoTestCase):
    def test_missing_frontmatter(self):
        path = self.root / "skills" / "fiftyone-bare" / "SKILL.md"
        path.parent.mkdir()
        path.write_text("# No frontmatter\n", encoding="utf-8")

        self.assert_skill_error("fiftyone-bare/SKILL.md", "missing YAML frontmatter")

    def test_unclosed_frontmatter(self):
        path = self.root / "skills" / "fiftyone-open" / "SKILL.md"
        path.parent.mkdir()
        path.write_text("---\nname: fiftyone-open\n", encoding="utf-8")

        self.assert_skill_error("not closed")

    def test_invalid_yaml(self):
        self.add_skill("fiftyone-bad-yaml", "name: [unclosed\ndescription: x")

        self.assert_skill_error("invalid YAML")

    def test_frontmatter_not_a_mapping(self):
        self.add_skill("fiftyone-list", "- just\n- a list")

        self.assert_skill_error("must be a YAML mapping")

    def test_missing_name(self):
        self.add_skill("fiftyone-no-name", "description: Does a thing.")

        self.assert_skill_error("missing required field 'name'")

    def test_missing_description(self):
        self.add_skill("fiftyone-no-desc", "name: fiftyone-no-desc")

        self.assert_skill_error("missing required field 'description'")

    def test_blank_description(self):
        self.add_skill("fiftyone-blank", "name: fiftyone-blank\ndescription: '  '")

        self.assert_skill_error("missing required field 'description'")

    def test_non_string_description(self):
        self.add_skill(
            "fiftyone-list-desc",
            "name: fiftyone-list-desc\ndescription:\n  - a\n  - b",
        )

        self.assert_skill_error("'description' must be a string")

    def test_invalid_name_format(self):
        self.add_skill("Bad_Name", "name: Bad_Name\ndescription: Does a thing.")

        self.assert_skill_error("invalid name 'Bad_Name'")

    def test_name_must_match_directory(self):
        self.add_skill(
            "fiftyone-dir", "name: fiftyone-other\ndescription: Does a thing."
        )

        self.assert_skill_error("does not match its directory 'fiftyone-dir'")

    def test_description_too_long(self):
        self.add_valid_skill("fiftyone-long", "x" * (ga.MAX_DESCRIPTION_LENGTH + 1))

        self.assert_skill_error("description is 1025 characters")

    def test_unsupported_field(self):
        self.add_skill(
            "fiftyone-extra",
            "name: fiftyone-extra\ndescription: Does a thing.\nemoji: x",
        )

        self.assert_skill_error("unsupported field(s) emoji")

    def test_reports_every_invalid_skill(self):
        self.add_skill("fiftyone-a", "description: Does a thing.")
        self.add_skill("fiftyone-b", "name: fiftyone-b")

        error = self.assert_skill_error()

        self.assertEqual(len(error.errors), 2)


class DuplicateNameTest(RepoTestCase):
    def test_duplicate_names_are_rejected(self):
        self.add_valid_skill("one/fiftyone-dup")
        self.add_valid_skill("two/fiftyone-dup")

        self.assert_skill_error(
            "skills/two/fiftyone-dup/SKILL.md",
            "duplicate skill name 'fiftyone-dup'",
            "also used by skills/one/fiftyone-dup/SKILL.md",
        )


class RenderTest(RepoTestCase):
    def test_title_handles_special_words(self):
        self.add_valid_skill("fiftyone-sdk-voodo-guide")

        (skill,) = ga.load_skills(self.root)

        self.assertEqual(skill.title, "FiftyOne SDK VOODO Guide")

    def test_generation_is_deterministic(self):
        self.add_valid_skill("fiftyone-b")
        self.add_valid_skill("fiftyone-a")
        skills = ga.load_skills(self.root)

        first = ga.update_agents_md(AGENTS_TEMPLATE, skills)
        second = ga.update_agents_md(first, ga.load_skills(self.root))

        self.assertEqual(first, second)
        self.assertLess(
            first.index("### FiftyOne A"), first.index("### FiftyOne B")
        )

    def test_text_outside_markers_is_preserved(self):
        self.add_valid_skill("fiftyone-a")

        result = ga.update_agents_md(AGENTS_TEMPLATE, ga.load_skills(self.root))

        self.assertTrue(result.startswith("# Agent Instructions\n"))
        self.assertTrue(result.endswith("## Prerequisites\n\nHand-written text.\n"))
        self.assertIn("Load the skill file at `skills/fiftyone-a/SKILL.md`", result)

    def test_compatibility_is_rendered_when_present(self):
        self.add_skill(
            "fiftyone-compat",
            "name: fiftyone-compat\ndescription: Does a thing.\n"
            "compatibility: Needs FiftyOne.",
        )

        result = ga.update_agents_md(AGENTS_TEMPLATE, ga.load_skills(self.root))

        self.assertIn("**Compatibility:** Needs FiftyOne.", result)

    def test_missing_markers(self):
        self.add_valid_skill("fiftyone-a")

        with self.assertRaises(ga.SkillError):
            ga.update_agents_md("# No markers\n", ga.load_skills(self.root))


class MainTest(RepoTestCase):
    def test_writes_then_check_passes(self):
        self.add_valid_skill("fiftyone-a")

        code, stdout, _ = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("Wrote AGENTS.md", stdout)
        self.assertIn("### FiftyOne A", self.agents_md())

        code, stdout, _ = self.run_main("--check")
        self.assertEqual(code, 0)
        self.assertIn("up to date", stdout)

    def test_check_fails_when_skill_added_without_regenerating(self):
        self.add_valid_skill("fiftyone-a")
        self.run_main()
        self.add_valid_skill("fiftyone-new")
        before = self.agents_md()

        code, _, stderr = self.run_main("--check")

        self.assertEqual(code, 1)
        self.assertIn("out of date", stderr)
        self.assertIn("+### FiftyOne New", stderr)
        self.assertEqual(self.agents_md(), before)

    def test_invalid_skill_fails_without_writing(self):
        self.add_skill("fiftyone-bad", "name: fiftyone-bad")

        code, _, stderr = self.run_main()

        self.assertEqual(code, 1)
        self.assertIn("missing required field 'description'", stderr)
        self.assertEqual(self.agents_md(), AGENTS_TEMPLATE)


class RepositoryTest(unittest.TestCase):
    def test_repository_agents_md_is_up_to_date(self):
        skills = ga.load_skills(ga.REPO_ROOT)
        current = (ga.REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertEqual(current, ga.update_agents_md(current, skills))


if __name__ == "__main__":
    unittest.main()
