"""Tests for context status and unify operations (no network I/O)."""
import pytest
from pathlib import Path
from aicfg.sdk import context as context_sdk


@pytest.fixture
def context_env(tmp_path, monkeypatch):
    """
    Creates isolated directories for context file testing.
    Monkeypatches Path.home() and git root detection.
    """
    user_home = tmp_path / "home"
    project_root = tmp_path / "project"

    # Create directory structure
    (user_home / ".config" / "ai-common").mkdir(parents=True)
    (user_home / ".claude").mkdir(parents=True)
    (user_home / ".gemini").mkdir(parents=True)
    (project_root / ".config" / "ai-common").mkdir(parents=True)
    (project_root / ".claude").mkdir(parents=True)
    (project_root / ".gemini").mkdir(parents=True)

    # Monkeypatch Path.home()
    monkeypatch.setattr(Path, "home", lambda: user_home)

    # Monkeypatch _get_git_root to return project_root
    monkeypatch.setattr(context_sdk, "_get_git_root", lambda: project_root)

    # Monkeypatch Path.cwd() for consistency
    monkeypatch.setattr(Path, "cwd", lambda: project_root)

    return user_home, project_root


# --- get_context_status tests ---

def test_get_status_user_unified(context_env):
    """User scope with symlinks pointing to CONTEXT.md."""
    user_home, _ = context_env

    # Create unified setup
    context_file = user_home / ".config" / "ai-common" / "CONTEXT.md"
    context_file.write_text("# Unified Context\n")

    claude_file = user_home / ".claude" / "CLAUDE.md"
    gemini_file = user_home / ".gemini" / "GEMINI.md"
    claude_file.symlink_to(context_file)
    gemini_file.symlink_to(context_file)

    result = context_sdk.get_context_status("user")

    assert "user" in result["scopes"]
    assert result["scopes"]["user"]["state"] == "unified"
    assert result["scopes"]["user"]["files"]["CLAUDE.md"]["points_to_unified"] is True
    assert result["scopes"]["user"]["files"]["GEMINI.md"]["points_to_unified"] is True


def test_get_status_user_separate(context_env):
    """User scope with separate CLAUDE.md and GEMINI.md files."""
    user_home, _ = context_env

    # Create separate files (not symlinks)
    claude_file = user_home / ".claude" / "CLAUDE.md"
    gemini_file = user_home / ".gemini" / "GEMINI.md"
    claude_file.write_text("# Claude Config\n")
    gemini_file.write_text("# Gemini Config\n")

    result = context_sdk.get_context_status("user")

    assert result["scopes"]["user"]["state"] == "not_unified"
    assert result["scopes"]["user"]["files"]["CLAUDE.md"]["exists"] is True
    assert result["scopes"]["user"]["files"]["CLAUDE.md"]["is_symlink"] is False
    assert result["scopes"]["user"]["files"]["GEMINI.md"]["exists"] is True
    assert result["scopes"]["user"]["files"]["GEMINI.md"]["is_symlink"] is False


def test_get_status_project_missing(context_env):
    """Project scope with no files present."""
    _, project_root = context_env

    result = context_sdk.get_context_status("project")

    assert result["scopes"]["project"]["state"] == "not_unified"
    assert result["scopes"]["project"]["files"]["CONTEXT.md"]["exists"] is False
    assert result["scopes"]["project"]["files"]["CLAUDE.md"]["exists"] is False
    assert result["scopes"]["project"]["files"]["GEMINI.md"]["exists"] is False


def test_get_status_both_scopes(context_env):
    """Default scope=None returns both user and project."""
    user_home, project_root = context_env

    # Create user file only
    (user_home / ".claude" / "CLAUDE.md").write_text("# User Claude\n")

    result = context_sdk.get_context_status(None)

    assert "user" in result["scopes"]
    assert "project" in result["scopes"]
    assert result["scopes"]["user"]["files"]["CLAUDE.md"]["exists"] is True
    assert result["scopes"]["project"]["files"]["CLAUDE.md"]["exists"] is False


# --- unify_context tests ---

def test_unify_user_claude_only(context_env):
    """Unify when only CLAUDE.md exists."""
    user_home, _ = context_env

    claude_file = user_home / ".claude" / "CLAUDE.md"
    claude_file.write_text("# Claude Rules\nBe helpful.\n")

    result = context_sdk.unify_context("user")

    assert result["success"] is True
    assert len(result["sources"]) == 1
    assert result["sources"][0]["name"] == "CLAUDE.md"

    # Verify symlink created
    assert claude_file.is_symlink()
    context_file = user_home / ".config" / "ai-common" / "CONTEXT.md"
    assert context_file.exists()
    assert "Claude Rules" in context_file.read_text()


def test_unify_user_gemini_only(context_env):
    """Unify when only GEMINI.md exists."""
    user_home, _ = context_env

    gemini_file = user_home / ".gemini" / "GEMINI.md"
    gemini_file.write_text("# Gemini Rules\nBe concise.\n")

    result = context_sdk.unify_context("user")

    assert result["success"] is True
    assert len(result["sources"]) == 1
    assert result["sources"][0]["name"] == "GEMINI.md"

    # Verify symlink created
    assert gemini_file.is_symlink()


def test_unify_user_both_files(context_env):
    """Unify when both CLAUDE.md and GEMINI.md exist."""
    user_home, _ = context_env

    claude_file = user_home / ".claude" / "CLAUDE.md"
    gemini_file = user_home / ".gemini" / "GEMINI.md"
    claude_file.write_text("# Claude Section\n")
    gemini_file.write_text("# Gemini Section\n")

    result = context_sdk.unify_context("user")

    assert result["success"] is True
    assert len(result["sources"]) == 2
    assert len(result["backups"]) == 2

    # Verify content merged
    context_file = user_home / ".config" / "ai-common" / "CONTEXT.md"
    content = context_file.read_text()
    assert "Claude Section" in content
    assert "Gemini Section" in content
    assert "CONTEXT IMPORTED FROM CLAUDE.md" in content
    assert "CONTEXT IMPORTED FROM GEMINI.md" in content


def test_unify_user_already_unified(context_env):
    """Idempotent - already symlinked returns success."""
    user_home, _ = context_env

    # Create unified setup first
    context_file = user_home / ".config" / "ai-common" / "CONTEXT.md"
    context_file.write_text("# Already Unified\n")

    claude_file = user_home / ".claude" / "CLAUDE.md"
    gemini_file = user_home / ".gemini" / "GEMINI.md"
    claude_file.symlink_to(context_file)
    gemini_file.symlink_to(context_file)

    result = context_sdk.unify_context("user")

    assert result["success"] is True
    assert "Already unified" in result["message"]


def test_unify_project_not_found(context_env):
    """No source files returns error."""
    _, project_root = context_env

    result = context_sdk.unify_context("project")

    assert result["success"] is False
    assert "No source files found" in result.get("error", "")
