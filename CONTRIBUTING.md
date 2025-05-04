Contributing to Da Vinci
========================

Thank you for your interest in contributing to Da Vinci! This guide will help you get started with contributing to the project.

Getting Started
---------------

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature or fix
4. Make your changes
5. Submit a pull request

Development Process
-------------------

Branching
---------

- Always create a new branch for your work
- Use descriptive branch names (e.g., `feature/add-s3-lifecycle-support`, `fix/event-bus-timeout-issue`)
- Keep your branches focused on a single feature or fix

Pull Requests
-------------

- Submit PRs from your feature branch to the main repository's `main` branch
- Provide a clear description of the changes in your PR
- Reference any related issues
- Ensure all tests pass before submitting
- Be responsive to feedback and questions during the review process

Code Style Guidelines
---------------------

### Python Style

- Use double quotes (`"`) for all strings
- Use single quotes (`'`) only for nested strings within double-quoted strings
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all public classes and functions

### Commit Messages

**IMPORTANT: Squash your commits!** Your PR should contain either:
- A single, well-crafted commit that encompasses all changes
- Multiple commits ONLY if they represent truly distinct, logical units of work

Before submitting your PR, use `git rebase -i` to squash your work-in-progress commits into meaningful commits.

#### Commit Message Format

1. **Title Line**: Concise description of the main change (aim for under 70 characters)
2. **Blank Line**: Always include a blank line after the title
3. **Details** (if needed): Use bullet points for multiple changes
4. Use active voice ("Add" not "Added", "Fix" not "Fixed")
5. Be specific and concise

#### Good Commit Message Examples:

Single change:
```
Add DynamoDB support for service discovery

Support using DynamoDB as an alternative to SSM for
service discovery. This enables better scalability
for large deployments.
```

Multiple related changes:
```
Fix event bus timeout handling

- Add proper timeout exception handling in event bus
- Report timeouts to exception trap service
- Update tests to cover timeout scenarios
- Fix issue where timeouts weren't being logged
```

#### Poor Commit Message Examples:

- "Fixed stuff"
- "Updated code"
- "WIP"
- "Fixed bug"
- "Made changes based on review feedback"
- Using past tense: "Added new feature" instead of "Add new feature"

Documentation
-------------

- Update the README.md if you're adding new features
- Add docstrings to all new functions and classes
- Update any relevant examples
- If you're adding new CDK constructs, include example usage
- Update the CHANGELOG.md following the existing format

Questions?
----------

If you have any questions about contributing, feel free to:

- Open an issue for discussion
- Ask in your pull request
- Reach out to the maintainers

Thank you for helping make Da Vinci better!