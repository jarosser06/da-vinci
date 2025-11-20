# Pull Request Format

Pull requests should be concise and objective. State what changed, link the issue, list new tests.

## Template

```markdown
## Summary
[1-2 sentences: what changed]

Closes #{issue_number}

## Changes
- [Change 1]
- [Change 2]
- [Change 3]

## Tests Added
- [Test 1]
- [Test 2]
```

## Guidelines

### Summary
- 1-2 sentences maximum
- State what changed
- Link issue with "Closes #N" or "Fixes #N"

### Changes
- List specific changes
- Be concrete, not vague
- No subjective language

### Tests Added
- List new tests added
- What each test validates
- Skip if no tests (documentation PRs)

## Objective Language

❌ **Avoid**: improved, enhanced, powerful, elegant, robust, clean, better, easily, simply

✅ **Use**: Specific descriptions

**Examples:**

❌ "Improved error handling"
✅ "Add retry logic for DynamoDB throttling"

❌ "Enhanced API"
✅ "Add batch_get_item and batch_write_item methods"

❌ "Better tests"
✅ "Add tests for error cases and retry scenarios"

## Examples

### Feature PR
```markdown
## Summary
Adds batch_get_item and batch_write_item methods to TableClient for multi-item operations.

Closes #123

## Changes
- Add TableClient.batch_get_item(keys: List[dict]) -> List[TableObject]
- Add TableClient.batch_write_item(items: List[TableObject]) -> None
- Add retry logic for unprocessed items (max 3 attempts, exponential backoff)
- Add BatchOperationError exception

## Tests Added
- batch_get_item: success, partial failure, oversized batch
- batch_write_item: success, total failure, oversized batch
- Retry scenarios with exponential backoff timing
```

### Bug Fix PR
```markdown
## Summary
Fixes Lambda timeout to read from settings.lambda_timeout instead of hardcoded 30 seconds.

Fixes #456

## Changes
- Update Application.add_lambda() to read settings.lambda_timeout
- Add 30-second default when not configured
- Add validation for 1-900 second range

## Tests Added
- Lambda uses configured timeout value
- Lambda uses default when not configured
- ValueError raised for invalid timeout
```

### Documentation PR
```markdown
## Summary
Adds batch operations documentation and examples.

Closes #789

## Changes
- Add batch operations section to docs/tables.rst
- Add batch_get_item usage example
- Add batch_write_item usage example
- Update API reference with batch methods

## Tests Added
N/A - Documentation only
```

## Quick Reference

| ❌ Don't Write | ✅ Write Instead |
|---------------|------------------|
| "Improved error handling" | "Add retry logic for throttling" |
| "Enhanced API" | "Add batch operation methods" |
| "Better performance" | "Reduce API calls from N to 1" |
| "Comprehensive tests" | "Add tests for X, Y, Z scenarios" |
| "Cleaned up code" | "Extract validation into TableValidator" |
