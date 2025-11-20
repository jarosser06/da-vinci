---
description: Create pull request with quality validation
skills:
  - pr-writing
  - testing
  - linting
  - github-operations
---

Create a pull request with quality validation.

Steps:
1. Run `./test.sh --coverage` to ensure tests pass and coverage ≥ 90%
2. Run `./lint.sh` to ensure zero lint errors
3. Review git diff to understand all changes
4. Extract issue number from branch name (if branch follows `issue/{number}-*` pattern)
5. Create PR description using pr-writing skill (summary, changes, tests added)
   - **IMPORTANT**: If issue number was found, include "Closes #{issue_number}" or "Fixes #{issue_number}" in PR body
6. Use github-operations skill to create PR via mcp__github

If quality gates fail (coverage < 90% or lint errors), report issues and do not create PR.

Note: PR body MUST reference the issue with "Closes #N" or "Fixes #N" to auto-link and close the issue on merge.
