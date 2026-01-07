# Gemini CLI - Common Configuration Assets

This repository hosts a curated collection of **generic, portable** configuration snippets and command definitions for the Gemini CLI.

## Purpose
The **individual contents** of this repository are designed to be portable and reusable on any workstation (personal or professional) where the Gemini CLI is used. It is **not** a workstation configuration repo and is not intended to be installed as a whole.

## Workflow
Users should cherry-pick individual files or definitions (e.g., custom slash commands) and manually integrate them into their local `~/.gemini` environment as needed.

## Contents
*   **/commands**: Portable slash command definitions (e.g., `commitall.toml`) designed to be environment-agnostic.

## Management Tool (`aicfg`)
This repository includes a Python CLI (`aicfg`) to manage the synchronization between this repository and your local `~/.gemini/commands` folder.

### Installation
Install the tool in **editable mode** to allow it to automatically locate this repository's root:

```bash
make install
```

**Why editable?** The tool uses relative path discovery to find the source-of-truth commands within this repo. An editable install preserves the link to this directory.

### Quick Start
Manage your slash commands with simple synchronization workflows:

| Command | Description |
| :--- | :--- |
| `aicfg cmds list` | Show status (Private, Available, Published, Dirty) |
| `aicfg cmds add <name> <prompt>` | Create a new command in your local XDG folder |
| `aicfg cmds publish <name>` | Promote a local command to this repository |
| `aicfg cmds install <name>` | Copy a command from this repo to your local XDG |
| `aicfg cmds diff <name>` | Show differences between local and repo versions |

**Example: Creating and Sharing a Command**
1. `aicfg cmds add my-fix "Explain this bug: {{context}}"` (Adds to `~/.gemini/commands/`)
2. `aicfg cmds publish my-fix` (Promotes to `./.gemini/commands/` for git commit)

## Development
To set up for development and run tests:

```bash
# Installs tool in editable mode and injects test dependencies
make install-dev

# Runs the integration tests
make test
```

**Test Strategy:**
The integration tests import and exercise the `aicfg.sdk` modules directly. They do **not** invoke the `aicfg` CLI executable via subprocess.
*   **Implication:** The package must be installed in the environment (editable mode recommended) for imports to work.
*   **Coverage:** Tests verify core logic and file operations but bypass Click command parsing.

**Note:** This uses `pipx` to manage the development environment.

## Security & Portability
*   **No local state:** This repo does not store `settings.json`, auth tokens, or absolute paths.
*   **No secrets:** All code is generic and safe for public use.

## Integration Notes
This configuration makes use of commands available in the [agentic-consult](https://github.com/krisrowe/agentic-consult) repository (e.g., `consult workspace`, `consult precommit`). 

### Future Plans
We plan to update the workflow commands to invoke user-configurable pre-commit commands (e.g., `npm run lint`, `ruff check .`) as defined in the project configuration.
