---
description: Complete workflow for working on a GitHub issue
skills:
  - github-operations
  - development
  - testing
---

Work on a GitHub issue with flexible TDD workflow.

Arguments:
- Issue number (required)

**IMPORTANT**: ALWAYS invoke the github-operations skill FIRST to fetch issue details.

Workflow:
1. **REQUIRED**: Invoke github-operations skill to fetch issue details from GitHub
2. Create branch: `issue/{number}-{brief-description}`
3. Ask user if they want tests written first (optional TDD)
4. If yes, use qa agent to create tests
5. Use developer agent to implement the solution
6. Validate with `./test.sh` and `./lint.sh`
7. Report completion and next steps (user can run /create-pr)

Note: TDD is encouraged but flexible - tests can be written before or after implementation based on user preference.
