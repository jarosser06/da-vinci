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

**IMPORTANT**: ALWAYS invoke the github-operations skill FIRST to fetch issue details.

Workflow:
1. **REQUIRED**: Invoke github-operations skill to fetch issue details from GitHub
2. **REQUIRED**: Assign the current user to the issue using mcp__github__update_issue
   - Get current GitHub username with: `gh api user --jq .login`
   - Update issue with assignees array containing the username
3. Create branch: `issue/<#>`
4. Use development skill to implement the solution
5. Run validation (`./test.sh` and `./lint.sh`) if applicable
6. **REQUIRED**: Invoke definition-of-done skill to validate work against issue requirements
7. Report completion and recommend running `/code-review` before creating PR
   - Format: "✅ Work complete. Run `/code-review` to review changes, then `/create-pr` when ready."

Note: Testing may not be applicable for all issues (e.g., documentation, infrastructure, configuration).
