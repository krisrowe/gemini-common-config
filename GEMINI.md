# Gemini CLI - aicfg Context

This repository includes the `aicfg` tool for managing slash commands and settings.

## Installation
To install the tool in editable mode, run the following from the repository root:

```bash
make install
```

## Testing
To run the test suite (automatically handles setup):

```bash
make test
```

**Test Strategy:**
The integration tests (`tests/integration/`) import and exercise the `aicfg.sdk` modules directly. They do **not** invoke the `aicfg` CLI executable via subprocess.
*   **Implication:** The package must be installed in the environment (editable mode recommended) for imports to work.
*   **Coverage:** Tests verify core logic and file operations but bypass Click command parsing.

If setup fails, ensure your environment allows package installation, then try:
```bash
make install-dev
```

## Maintenance Note
**IMPORTANT:** Keep `README.md`, `Makefile`, and this `GEMINI.md` in sync regarding installation and testing procedures. If the setup logic changes in the Makefile, update the documentation in both files immediately.

## Structure
- `aicfg/sdk`: Core logic for configuration and settings management.
- `aicfg/mcp`: MCP server implementation.
- `aicfg/cli`: CLI interface wrappers.