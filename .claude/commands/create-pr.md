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
4. Create PR description using pr-writing skill (summary, changes, tests added)
5. Use github-operations skill to create PR via mcp__github

If quality gates fail (coverage < 90% or lint errors), report issues and do not create PR.
