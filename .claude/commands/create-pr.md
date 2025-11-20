---
description: Create pull request with quality validation
skills:
  - pr-writing
  - testing
  - linting
  - github-operations
---

Create a pull request with quality validation.

**CRITICAL**: You MUST activate ALL skills listed in frontmatter using the Skill tool before proceeding.

Steps:
1. **REQUIRED**: Activate skills: `Skill(pr-writing)`, `Skill(testing)`, `Skill(linting)`, `Skill(github-operations)`
2. Run `./test.sh --coverage` - fail if coverage < 90%
3. Run `./lint.sh` - fail if errors exist
4. Review git diff to understand changes
5. Extract issue number from branch name (issue/<#> pattern)
6. Create concise PR description following pr-writing skill format:
   - Summary: 1-2 sentences, what changed
   - Changes: Specific changes made
   - Tests Added: New tests added (what they validate)
   - Include "Closes #{number}" or "Fixes #{number}"
7. Create PR via mcp__github

If tests or linting fail, report and stop.
