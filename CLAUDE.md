# Linting Standards

## Core Principle

**All linting errors must be resolved before committing code.**

Do not ignore, suppress, or bypass linting checks unless explicitly instructed by the user.

## Workflow

1. **Run the project's linter** - Use whatever linting tools the project has configured
2. **Fix all reported issues** - Address errors, warnings, and style violations
3. **Verify clean output** - Re-run linter to confirm all issues are resolved
4. **Only then commit** - Linting must pass before creating commits

## When Linting Errors Occur

- **Fix the issue** - Don't add ignore comments or suppress warnings
- **Follow project standards** - Respect the project's linting configuration
- **Ask for clarification** - If an error seems incorrect, ask the user rather than bypassing it

## Acceptable Exceptions

You may ignore linting errors only when:
- The user explicitly instructs you to do so
- The user provides specific ignore directives or suppression comments to add

Otherwise, treat all linting errors as blockers that must be resolved.

# Bug Fix Tests

**Before fixing a bug, write a test that reproduces it and fails.** Then fix the bug and confirm the test passes.

The failing test proves the bug exists and prevents regression. Skip only if the user waives it or the change has no behavioral impact (e.g. typo in a comment).

# Use Serena for Codebase Work

**Use the `serena` MCP server for all codebase exploration, navigation, and symbol lookup.** Do not rely on memory or assumptions about code structure — query serena.

# Use Context7 for Documentation

**Use the `context7` MCP server to look up library and API documentation.** Never assume an API's behavior — check the docs before writing or recommending code that depends on it.

# No AI Attribution

**Never include attribution for AI assistance in commits, pull requests, or any code contributions.**

Do not add:
- `Co-Authored-By: Claude`
- `Co-Authored-By: AI Assistant`
- Any similar AI attribution
- Comments crediting AI assistance

Code contributions should reflect the repository owner's work. AI assistance is a tool, not a contributor.


# Use Runbook for Project Tasks

**Use the `runbook` MCP server for all project task automation** — dev servers, builds, linting, type checking, testing, and any other tooling exposed under `.runbook/*.yaml`. Never invoke those underlying commands (e.g. `tsc`, `eslint`, `vitest`, `vite`, `astro`, `next`, `docker compose`, `ruff`, `mypy`) directly via Bash when an equivalent runbook task exists.

Check available tasks with the runbook MCP tools before reaching for Bash. If a task is missing, add it to the appropriate `.runbook/*.yaml` rather than working around it.


You must use the runbook MCP tools for all Python linting, formatting, type checking, and dead-code detection operations. Never run ruff, mypy, black, isort, or vulture commands directly via Bash. Available runbook tasks: py-ruff, py-black, py-isort, py-mypy, py-vulture, py-vulture-whitelist, py-uv-sync.
# NO INLINE LINT / TYPE / DEAD-CODE SUPPRESSIONS — HARD RULE

**NEVER** write `# noqa`, `# noqa: <code>`, `# type: ignore`, `# type: ignore[<code>]`,
`# pyright: ignore`, `# pylint: disable`, `# vulture: ignore`, `# noinspection`,
`# fmt: off` / `# fmt: on`, `# ruff: noqa`, `# mypy: ignore-errors`, or any
equivalent inline suppression comment. **NO EXCEPTIONS.**

If a tool reports an issue, do exactly one of:

1. **Fix the actual problem.** The tool is telling you something real.
2. **Delete the code.** If vulture says it is dead, it is almost always dead. Remove it.
3. **Use the project-level whitelist mechanism.** For genuine vulture false positives
   (framework hooks, dynamic attribute access), append to `.vulture_whitelist.py`
   via the `py-vulture-whitelist` runbook task — never inline. For ruff per-file
   exceptions, use `[tool.ruff.lint.per-file-ignores]` in `pyproject.toml`.
4. **Refactor.** If a type checker is fighting you, your types are wrong.

Inline suppressions hide bugs, spread, and defeat CI. Reject any PR that adds one.

See `.claude/rules/python/no-suppressions.md` for the full reference.
