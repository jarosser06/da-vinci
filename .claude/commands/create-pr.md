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
1. Run `./test.sh --coverage` - fail if coverage < 90%
2. Run `./lint.sh` - fail if errors exist
3. Review git diff to understand changes
4. Extract issue number from branch name (issue/<#> pattern)
5. Create concise PR description:
   - Summary: 1-2 sentences, what changed
   - Changes: Specific changes made
   - Tests Added: New tests added (what they validate)
   - Include "Closes #{number}" or "Fixes #{number}"
6. Create PR via mcp__github

If tests or linting fail, report and stop.
