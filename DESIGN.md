# Design Decisions

Architectural decisions and rationale for the `aicfg` tool.

## SDK-First Architecture

All business logic lives in `aicfg/sdk/`. Both CLI (`aicfg/cli/`) and MCP server (`aicfg/mcp/`) are thin presentation layers that:

- Call SDK functions directly
- Format output for their respective consumers (terminal vs JSON)
- Never duplicate logic between CLI and MCP

This ensures consistent behavior regardless of invocation method.

## MCP Tool Exposure Policy

Not all CLI commands are exposed as MCP tools. We deliberately limit the MCP toolspace to operations that:

1. **Are frequently used** in agent workflows
2. **Can be reliably automated** without extensive user involvement
3. **Don't pose risks** when invoked by AI agents autonomously

### Context Management Commands (CLI-only)

The following commands are intentionally **not exposed as MCP tools**:

| Command | Reason |
|---------|--------|
| `aicfg context unify` | Infrequent operation; merges system prompt files |
| `aicfg context analyze` | Analyzes agent's own system prompt |
| `aicfg context revise` | Modifies agent's own system prompt |

**Rationale:** These commands manage the AI assistant's context/system prompt files. Exposing them as MCP tools would:

- Allow AI agents to analyze and manipulate their own instructions
- Enable autonomous modification of system prompts without user oversight
- Create potential for unintended self-modification loops

Users who need these operations should invoke them explicitly via the CLI where the action is visible and intentional.

### Context Include Paths (CLI-only)

The `aicfg paths` commands for managing `context.includeDirectories` are **not exposed as MCP tools**.

**Rationale:**

1. **Security**: Including directories exposes their contents to the AI agent. This decision should be explicit and user-driven, not agentic.

2. **Performance**: Each included path adds to context size and processing time. Unnecessary paths degrade response quality and speed.

3. **Context pollution**: Indiscriminate path inclusion creates noise that dilutes relevant context, making the agent less effective.

4. **User-scoped paths are an antipattern**: Paths should generally be project-scoped (relevant to the current repo). User-scoped paths that apply globally across all projects are rarely appropriate and risk exposing unrelated content.

**CLI behavior:**
- Default scope: `project`
- User scope: Available via `--scope user` flag for rare cases
- MCP: No tool provided; path configuration requires explicit CLI action

### MCP Tools Provided

Operations suitable for agent automation:

| Tool | Purpose |
|------|---------|
| `list_mcp_servers` | Query registered servers (read-only) |
| `list_slash_commands` | Query available commands (read-only) |
| `add_slash_command` | Create new commands (additive, user-visible) |
| `get_slash_command` | Retrieve command definitions (read-only) |
| `check_mcp_server_startup` | Diagnose server issues (read-only) |

## Scope Conventions

Operations that support multiple scopes follow these conventions:

- `user` scope: `~/.config/...` or `~/.gemini/...` (user-level settings)
- `project` scope: `./.gemini/...` or `./.config/...` (repo-level settings)
- Default behavior when scope is omitted varies by operation:
  - **Read operations**: Show all scopes combined
  - **Write operations**: Use project scope if in git repo, else user scope
