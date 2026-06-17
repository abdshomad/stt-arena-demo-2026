# Agent Guidelines

## Crucial Rule: Do Not Edit Git Submodules

To preserve the integrity of the repository's dependency model, all AI agents operating in this workspace must adhere to the following rule:

> [!IMPORTANT]
> **NEVER edit, update, delete, or commit changes to files inside the Git submodules.**

### Reasons
1. **Upstream Alignment**: Submodules are independent repositories maintained separately. Directly editing files within them diverges from upstream sources.
2. **Detached HEAD & Versioning**: Modifying files inside submodules can lead to detached HEAD states and make dependency version management complex and error-prone.
3. **Clean Commits**: Project modifications should strictly focus on the parent repository. Any changes to submodules must be done by modifying the submodule upstream or updating the tracked commit reference in the parent repository.

### Tracked Submodules
- [autonomous-coding-agents](../stt-arena-autonomously/autonomous-coding-agents)

## Python Dependency Management Guidelines

To ensure fast, clean, and reproducible Python environments, all AI agents must always use `uv` to manage Python dependencies:
- Use `uv init` to initialize a new Python project/workspace.
- Use `uv add <package>` to add dependencies (do not use `pip install` directly).
- Use `uv remove <package>` to remove dependencies.
- Use `uv sync` to synchronize the virtual environment with `pyproject.toml` or `uv.lock`.
- Use `uv run <command>` or `uv run <script.py>` to run scripts in the virtual environment.

## Issue Tracking Guidelines

To ensure transparent issue tracking and maintainable debugging logs, all AI agents must record every encountered and resolved issue or bug:
- Save details of each issue inside a dedicated markdown file in the [issues/](issues) directory.
- Name the files sequentially starting with a 3-digit number (e.g. `001-issue-description.md`, `002-another-issue.md`).
- Each issue file should document:
  - **Symptoms**: Visual glitches, traceback, logs, or error codes.
  - **Root Cause**: Rationale and underlying code explanation.
  - **Resolution**: Changes made, fixes applied, or instructions on how it was corrected.

## Explicit Testing & Browser Diagnostics Guidelines

When the user explicitly asks to test the application or verify the frontend interface, agents must perform browser-based diagnostics/automation (such as using Chrome DevTools MCP tools) and capture screenshots:
- **Location**: Save captured screenshots in the `/screenshots/` directory in the repository root.
- **Directory & File Hierarchy**: Number directories, subdirectories, and files sequentially to maintain order:
  - Directory: `/screenshots/<3-digit-seq>-<feature-group>/` (e.g. `/screenshots/001-ui-verification/`)
  - Sub-directory: `/screenshots/<3-digit-seq>-<feature-group>/<3-digit-seq>-<sub-feature>/` (e.g. `/screenshots/001-ui-verification/001-transcription/`)
  - Screenshot filename: `<3-digit-seq-step>-<description>.png` (e.g. `001-initial-load.png`, `002-transcription-success.png`)
- **Execution**: Use available browser testing/automation tools to interact with the frontend, inspect DOM nodes, audit accessibility, and verify correctness of visual assets and page flows.



