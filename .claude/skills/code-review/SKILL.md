# Code Review

**Description**: Perform comprehensive code reviews for da_vinci contributions. Use when reviewing changes before PR or merge.

## When to Use This Skill

- Reviewing code changes before creating PR
- Self-review of your own changes
- Checking for common issues
- Validating code quality

## Quick Reference

### Review Checklist
- Code follows PEP 8 and project standards
- Type hints on all public APIs
- Docstrings on public functions/classes
- No hardcoded values
- Tests cover new code (≥90% coverage)
- **Tests validate behavior, not just coverage**:
  - Different parameter combinations tested
  - Edge cases covered (boundary conditions, errors, nulls)
  - Integration scenarios validated
  - Assertions check actual behavior, not just existence
- CHANGELOG.md updated

## Resource Guides

### 📖 [Review Checklist](resources/checklist.md)
Comprehensive code review checklist including detailed test quality requirements.

**Use when**: Performing a code review.

### 📖 [Test Quality Guide](resources/test-quality.md)
In-depth guide for reviewing test quality beyond coverage percentages. Includes examples of good vs. bad tests, edge case coverage, parameter combinations, and behavioral validation.

**Use when**: Reviewing tests to ensure they're comprehensive, not just achieving coverage numbers.

### 📖 [Common Issues](resources/common-issues.md)
Common problems to watch for.

**Use when**: Looking for specific anti-patterns.

### 📖 [Review Format](resources/review-format.md)
How to format review feedback.

**Use when**: Providing review comments.

## Key Principles

1. **Constructive Feedback**: Focus on improvement, not criticism
2. **Explain Why**: Don't just point out issues, explain the reasoning
3. **Check Test Quality**: Ensure tests are comprehensive, not just achieving coverage numbers
   - Verify different parameter combinations are tested
   - Check edge cases and error handling are covered
   - Validate assertions check behavior, not just existence
   - Ensure integration scenarios are tested
4. **Verify Standards**: Code follows project conventions
