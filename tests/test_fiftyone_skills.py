"""Unit tests for fiftyone_skills — pure functions and filesystem only."""

from __future__ import annotations

import hashlib
import logging
import subprocess
from pathlib import Path

import pytest

from fiftyone_skills import (
    __version__,
    CLI_DESCRIPTION,
    _git_blob_sha,
    _setup_logging,
    copy_skills,
    get_install_dir,
)


class TestGetInstallDir:
    @pytest.mark.parametrize(
        "agent,expected_sub",
        [
            ("claude", ".claude/skills"),
            ("codex", ".codex/skills"),
            ("cursor", ".cursor/skills"),
            ("copilot", ".github/copilot/skills"),
            ("Claude", ".claude/skills"),  # uppercase normalised to key
        ],
    )
    def test_local_agent_paths(self, agent: str, expected_sub: str) -> None:
        assert get_install_dir("local", agent) == Path.cwd() / expected_sub

    def test_global_env(self) -> None:
        assert get_install_dir("global", "claude") == Path.home() / ".claude" / "skills"

    @pytest.mark.parametrize(
        "env,base", [("local", Path.cwd()), ("global", Path.home())]
    )
    @pytest.mark.parametrize("agent", [None, "none", "None"])
    def test_none_agent_variants(self, env: str, base: Path, agent: str | None) -> None:
        assert get_install_dir(env, agent) == base / ".agents" / "skills"

    def test_invalid_env_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid env"):
            get_install_dir("bad_env", "claude")

    def test_invalid_agent_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid agent"):
            get_install_dir("local", "vscode")


class TestGitBlobSha:
    @pytest.mark.parametrize(
        "content,expected",
        [
            (b"", hashlib.sha1(b"blob 0\0").hexdigest()),
            (b"hello world\n", hashlib.sha1(b"blob 12\0hello world\n").hexdigest()),
        ],
    )
    def test_hash_computation(
        self, tmp_path: Path, content: bytes, expected: str
    ) -> None:
        f = tmp_path / "test.bin"
        f.write_bytes(content)
        assert _git_blob_sha(f) == expected


class TestCopySkills:
    def test_copy_and_count(self, fake_skills_src: Path, tmp_path: Path) -> None:
        dest = tmp_path / "dest"
        count = copy_skills(fake_skills_src, dest)
        assert count == 2
        assert (dest / "fiftyone-alpha").is_dir()
        assert (dest / "fiftyone-beta").is_dir()
        assert not (dest / ".hidden").exists()

    def test_creates_dest_and_overwrites(
        self, fake_skills_src: Path, tmp_path: Path
    ) -> None:
        dest = tmp_path / "dest"
        assert not dest.exists()
        copy_skills(fake_skills_src, dest)
        assert dest.is_dir()

        stale = dest / "fiftyone-alpha" / "stale.md"
        stale.write_text("stale")
        copy_skills(fake_skills_src, dest)
        assert not stale.exists()
        assert (dest / "fiftyone-alpha" / "SKILL.md").exists()


class TestSetupLogging:
    def test_setup_logging(self, capsys: pytest.CaptureFixture[str]) -> None:
        _setup_logging()
        root = logging.getLogger()
        assert len(root.handlers) == 2
        # Idempotent: second call clears and re-adds, count stays 2
        _setup_logging()
        assert len(root.handlers) == 2

        log = logging.getLogger("test_routing_unique")
        log.info("info-only-message")
        log.warning("warning-only-message")
        captured = capsys.readouterr()
        assert "info-only-message" in captured.out
        assert "info-only-message" not in captured.err
        assert "warning-only-message" in captured.err
        assert "warning-only-message" not in captured.out


class TestCLI:
    def test_no_args_creates_nothing(self, tmp_path: Path) -> None:
        result = subprocess.run(["fiftyone-skills"], cwd=tmp_path, capture_output=True)
        assert result.returncode != 0
        assert not any(tmp_path.iterdir())

    def test_install_local_claude(self, tmp_path: Path) -> None:
        subprocess.run(
            ["fiftyone-skills", "env=local", "agent=claude"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )
        assert (tmp_path / ".claude" / "skills").is_dir()

    @pytest.mark.parametrize(
        "flag,expected",
        [
            ("--version", f"fiftyone-skills {__version__}"),
            ("--help", CLI_DESCRIPTION),
        ],
    )
    def test_flags(self, flag: str, expected: str) -> None:
        result = subprocess.run(
            ["fiftyone-skills", flag], capture_output=True, text=True
        )
        assert expected in result.stdout
