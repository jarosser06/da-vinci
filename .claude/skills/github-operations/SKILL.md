# GitHub Operations

**Description**: GitHub workflow operations via MCP. Use when working with issues, PRs, and GitHub API.

## When to Use This Skill

- Fetching GitHub issues
- Creating or updating issues
- Listing pull requests
- Assigning issues
- Working with GitHub API

## Quick Reference

### GitHub MCP Server
- Always use mcp__github for GitHub operations
- Never hardcode repository names
- Detect repo from git remote
- Use GitHub CLI (gh) for operations

### Common Operations
- List issues assigned to user
- Fetch issue details
- Create new issues
- Update issue status
- List pull requests
- Get PR information

## Key Principles

1. **Auto-Detect Repo**: Always detect repository from git remote, never hardcode
2. **Use MCP Server**: All GitHub operations through mcp__github
3. **Require Token**: GitHub personal access token required for authentication
4. **Handle Errors Gracefully**: Check for auth failures and network issues
