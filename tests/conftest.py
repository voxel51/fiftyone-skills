"""Shared pytest fixtures for fiftyone-skills tests."""

from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def reset_root_logger() -> Generator[None, None, None]:
    """Save and restore root logger handlers + level around each test."""
    root = logging.getLogger()
    old_handlers = root.handlers[:]
    old_level = root.level
    yield
    root.handlers = old_handlers
    root.level = old_level


@pytest.fixture
def fake_skills_src(tmp_path: Path) -> Path:
    """Create a fake skills source with 2 skill dirs and one hidden dir."""
    src = tmp_path / "skills_src"
    src.mkdir()
    (src / "fiftyone-alpha").mkdir()
    (src / "fiftyone-alpha" / "SKILL.md").write_text("# Alpha")
    (src / "fiftyone-beta").mkdir()
    (src / "fiftyone-beta" / "SKILL.md").write_text("# Beta")
    (src / ".hidden").mkdir()
    return src
