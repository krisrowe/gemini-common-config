"""Tests for context analyze and revise operations (mocked Gemini API)."""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
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

    # Set fake API key
    monkeypatch.setenv("GEMINI_API_KEY", "fake-api-key-for-testing")

    return user_home, project_root


@pytest.fixture
def mock_gemini_response():
    """Create a mock Gemini client and response."""
    mock_response = MagicMock()
    mock_response.text = "Mocked response from Gemini."

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    # Create mock genai module that will be imported as `from google import genai`
    mock_genai = MagicMock()
    mock_genai.Client.return_value = mock_client

    # Create mock google module with genai as attribute
    mock_google = MagicMock()
    mock_google.genai = mock_genai

    return mock_google, mock_genai, mock_client, mock_response


# --- analyze_context tests ---

def test_analyze_user_unified(context_env, mock_gemini_response):
    """Analyze unified user context."""
    user_home, _ = context_env
    mock_google, mock_genai, mock_client, mock_response = mock_gemini_response

    # Create unified setup
    context_file = user_home / ".config" / "ai-common" / "CONTEXT.md"
    context_file.write_text("# User Context\nBe helpful and concise.\n")
    (user_home / ".claude" / "CLAUDE.md").symlink_to(context_file)
    (user_home / ".gemini" / "GEMINI.md").symlink_to(context_file)

    mock_response.text = "The user context emphasizes being helpful and concise."

    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        result = context_sdk.analyze_context("user", "Summarize the context")

    assert result["success"] is True
    assert result["response"] == "The user context emphasizes being helpful and concise."
    assert result["scope"] == "user"


def test_analyze_project_with_gemini(context_env, mock_gemini_response):
    """Analyze project with only GEMINI.md present."""
    _, project_root = context_env
    mock_google, mock_genai, mock_client, mock_response = mock_gemini_response

    gemini_file = project_root / ".gemini" / "GEMINI.md"
    gemini_file.write_text("# Project Rules\nFollow coding standards.\n")

    mock_response.text = "Project rules focus on coding standards."

    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        result = context_sdk.analyze_context("project", "What are the rules?")

    assert result["success"] is True
    assert "coding standards" in result["response"]


def test_analyze_project_with_both(context_env, mock_gemini_response):
    """Analyze project with both CLAUDE.md and GEMINI.md."""
    _, project_root = context_env
    mock_google, mock_genai, mock_client, mock_response = mock_gemini_response

    (project_root / ".claude" / "CLAUDE.md").write_text("# Claude Rules\n")
    (project_root / ".gemini" / "GEMINI.md").write_text("# Gemini Rules\n")

    mock_response.text = "Both Claude and Gemini rules are defined."

    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        result = context_sdk.analyze_context("project", "Describe all rules")

    assert result["success"] is True


def test_analyze_all_scopes(context_env, mock_gemini_response):
    """Analyze scope='all' includes both user and project."""
    user_home, project_root = context_env
    mock_google, mock_genai, mock_client, mock_response = mock_gemini_response

    (user_home / ".claude" / "CLAUDE.md").write_text("# User Claude\n")
    (project_root / ".gemini" / "GEMINI.md").write_text("# Project Gemini\n")

    mock_response.text = "Analysis covers both user and project scopes."

    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        result = context_sdk.analyze_context("all", "Analyze everything")

    assert result["success"] is True
    assert result["scope"] == "all"


def test_analyze_not_found(context_env, mock_gemini_response):
    """Analyze with no .md files still works (returns status showing missing)."""
    _, project_root = context_env
    mock_google, mock_genai, mock_client, mock_response = mock_gemini_response

    mock_response.text = "No context files found in project scope."

    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        result = context_sdk.analyze_context("project", "What's configured?")

    # analyze_context doesn't fail on missing files - it reports the status
    assert result["success"] is True


# --- revise_context tests ---

def test_revise_user_unified(context_env, mock_gemini_response):
    """Revise user CONTEXT.md successfully."""
    user_home, _ = context_env
    mock_google, mock_genai, mock_client, mock_response = mock_gemini_response

    context_file = user_home / ".config" / "ai-common" / "CONTEXT.md"
    context_file.write_text("# Old Content\nOriginal text.\n")

    mock_response.text = "# New Content\nRevised text with improvements.\n"

    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        result = context_sdk.revise_context("user", "Improve the content")

    assert result["success"] is True
    assert "backup" in result

    # Verify file was updated
    new_content = context_file.read_text()
    assert "Revised text" in new_content

    # Verify backup created
    backup_file = context_file.with_suffix(".md.bak")
    assert backup_file.exists()
    assert "Old Content" in backup_file.read_text()


def test_revise_project_with_context(context_env, mock_gemini_response):
    """Revise project CONTEXT.md."""
    _, project_root = context_env
    mock_google, mock_genai, mock_client, mock_response = mock_gemini_response

    context_file = project_root / ".config" / "ai-common" / "CONTEXT.md"
    context_file.write_text("# Project Config\n")

    mock_response.text = "# Updated Project Config\nWith new sections.\n"

    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        result = context_sdk.revise_context("project", "Add new sections")

    assert result["success"] is True


def test_revise_not_found(context_env, mock_gemini_response):
    """Revise with no file to revise returns error."""
    _, project_root = context_env
    mock_google, mock_genai, _, _ = mock_gemini_response

    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        result = context_sdk.revise_context("project", "Try to revise")

    assert result["success"] is False
    assert "No context file found" in result["error"]


def test_revise_all_not_allowed(context_env):
    """Revise with scope='all' is rejected."""
    result = context_sdk.revise_context("all", "Try to revise all")

    assert result["success"] is False
    assert "Cannot revise 'all'" in result["error"]


def test_revise_update_declined(context_env, mock_gemini_response):
    """Gemini returns a refusal instead of updated content."""
    user_home, _ = context_env
    mock_google, mock_genai, mock_client, mock_response = mock_gemini_response

    context_file = user_home / ".config" / "ai-common" / "CONTEXT.md"
    original_content = "# Important Rules\nDo not modify these.\n"
    context_file.write_text(original_content)

    # Simulate Gemini declining to make harmful changes
    mock_response.text = (
        "I cannot make that change. The request asks me to remove important "
        "safety guidelines which would be inappropriate. Please reconsider "
        "the modification you're requesting."
    )

    with patch.dict(sys.modules, {"google": mock_google, "google.genai": mock_genai}):
        result = context_sdk.revise_context("user", "Remove all safety rules")

    # Current implementation writes whatever Gemini returns.
    # This test documents that behavior - the "revision" contains refusal text.
    # A future enhancement could detect refusals and return success=False.
    assert result["success"] is True

    # The file now contains the refusal message (not ideal but current behavior)
    new_content = context_file.read_text()
    assert "cannot make that change" in new_content

    # Original preserved in backup
    backup_file = context_file.with_suffix(".md.bak")
    assert "Important Rules" in backup_file.read_text()
