---
description: Complete workflow for working on a GitHub issue
skills:
  - github-operations
  - development
  - testing
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
3. Create branch: `issue/{number}-{brief-description}`
4. Use development skill to implement the solution
5. Run validation (`./test.sh` and `./lint.sh`) if applicable
6. Report completion and next steps (user can run /create-pr)

Note: Testing may not be applicable for all issues (e.g., documentation, infrastructure, configuration).
