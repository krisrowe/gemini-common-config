# Gemini CLI - Common Configuration Assets

This repository hosts a curated collection of **generic, portable** configuration snippets and command definitions for the Gemini CLI.

## Purpose
The **individual contents** of this repository are designed to be portable and reusable on any workstation (personal or professional) where the Gemini CLI is used. It is **not** a workstation configuration repo and is not intended to be installed as a whole.

## Workflow
Users should cherry-pick individual files or definitions (e.g., custom slash commands) and manually integrate them into their local `~/.gemini` environment as needed.

## Contents
*   **/commands**: Portable slash command definitions (e.g., `commitall.toml`) designed to be environment-agnostic.

## Security & Portability
*   **No local state:** This repo does not store `settings.json`, auth tokens, or absolute paths.
*   **No secrets:** All code is generic and safe for public use.

## Integration Notes
This configuration makes use of commands available in the [agentic-consult](https://github.com/krisrowe/agentic-consult) repository (e.g., `consult workspace`, `consult precommit`). 

### Future Plans
We plan to update the workflow commands to invoke user-configurable pre-commit commands (e.g., `npm run lint`, `ruff check .`) as defined in the project configuration.
