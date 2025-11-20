---
description: Complete workflow for working on a GitHub issue
skills:
  - github-operations
  - development
  - testing
  - definition-of-done
---

Work on a GitHub issue.

Arguments:
- Issue number (required)

**CRITICAL**: You MUST activate ALL skills listed in frontmatter using the Skill tool before proceeding.

Workflow:
1. **REQUIRED**: Activate skills: `Skill(github-operations)`, `Skill(development)`, `Skill(testing)`, `Skill(definition-of-done)`
2. **REQUIRED**: Use github-operations skill to fetch issue details from GitHub
3. **REQUIRED**: Assign the current user to the issue using mcp__github__update_issue
   - Get current GitHub username with: `gh api user --jq .login`
   - Update issue with assignees array containing the username
4. Create branch: `issue/<#>`
5. Use development skill to implement the solution
6. Run validation (`./test.sh` and `./lint.sh`) if applicable
7. **REQUIRED**: Use definition-of-done skill to validate work against issue requirements
8. Report completion and recommend running `/code-review` before creating PR
   - Format: "✅ Work complete. Run `/code-review` to review changes, then `/create-pr` when ready."

Note: Testing may not be applicable for all issues (e.g., documentation, infrastructure, configuration).
