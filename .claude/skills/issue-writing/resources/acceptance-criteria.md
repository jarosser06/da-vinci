# Writing Well-Defined Acceptance Criteria

Acceptance criteria define when an issue is complete. They must be objective, verifiable, and specific.

## Core Principles

### 1. Yes/No Verifiable
Every criterion must be answerable with "yes" or "no" - no subjective judgment required.

✅ **Good:**
```markdown
- [ ] TableClient.batch_get_item() method exists
- [ ] Method accepts List[dict] parameter
- [ ] Method returns List[TableObject]
- [ ] Method handles up to 100 items
```

❌ **Bad:**
```markdown
- [ ] Batch get method works well
- [ ] API is easy to use
- [ ] Error handling is robust
- [ ] Implementation is clean
```

### 2. Specific and Measurable
Avoid vague terms that require interpretation.

✅ **Good:**
```markdown
- [ ] Lambda timeout reads from settings.lambda_timeout
- [ ] Default timeout is 30 seconds when not configured
- [ ] Error raised when timeout exceeds AWS maximum (900s)
```

❌ **Bad:**
```markdown
- [ ] Lambda timeout configuration improved
- [ ] Timeout handling is better
- [ ] Configuration is flexible
```

### 3. Behavior, Not Implementation
Focus on what, not how (unless implementation is constrained).

✅ **Good:**
```markdown
- [ ] Retry failed items up to 3 times
- [ ] Wait time increases exponentially (1s, 2s, 4s)
- [ ] Raise BatchOperationError after final failure
```

❌ **Bad:**
```markdown
- [ ] Create RetryHandler class
- [ ] Use decorator pattern for retries
- [ ] Store retry state in instance variable
```

### 4. Don't Repeat Project Standards
Test coverage, linting, and code quality standards are already defined.

✅ **Good:**
```markdown
- [ ] Tests cover timeout scenarios (0s, 30s, 300s, 900s, 1000s)
- [ ] Tests verify default behavior when setting not configured
```

❌ **Bad:**
```markdown
- [ ] Tests have ≥90% coverage (already project standard)
- [ ] Code passes linting (already enforced by ./lint.sh)
- [ ] Type hints on all methods (already code review standard)
- [ ] Docstrings on public APIs (already code review standard)
- [ ] No hardcoded values (already code review standard)
```

## Acceptance Criteria Patterns

### Feature Implementation Criteria

Focus on functional behavior:

```markdown
**Acceptance Criteria:**
- [ ] {Method/function name} {does what}
- [ ] {Input validation} {behavior}
- [ ] {Edge case} {is handled}
- [ ] {Error condition} {raises specific exception}
- [ ] {Integration point} {works as expected}
- [ ] CHANGELOG.md updated under "Unreleased"
```

**Example:**
```markdown
**Acceptance Criteria:**
- [ ] batch_get_item() retrieves multiple items in single call
- [ ] Method raises ValueError when keys list exceeds 100 items
- [ ] Unprocessed keys are retried with exponential backoff
- [ ] BatchOperationError raised when all retries fail
- [ ] Method returns List[TableObject] in same order as input keys
- [ ] CHANGELOG.md updated under "Unreleased"
```

### Bug Fix Criteria

Focus on behavior change:

```markdown
**Acceptance Criteria:**
- [ ] {Bug} no longer occurs
- [ ] {Expected behavior} happens instead
- [ ] {Edge cases from bug} are handled
- [ ] Regression test added for {specific scenario}
- [ ] CHANGELOG.md updated under "Unreleased"
```

**Example:**
```markdown
**Acceptance Criteria:**
- [ ] Lambda uses settings.lambda_timeout value when set
- [ ] Lambda uses 30-second default when settings.lambda_timeout not set
- [ ] Deployed Lambda configuration matches settings value
- [ ] Test verifies timeout configuration for both cases
- [ ] CHANGELOG.md updated under "Unreleased"
```

### Documentation Criteria

Be specific about content and location:

```markdown
**Acceptance Criteria:**
- [ ] {Specific content} added to {specific file}
- [ ] Code example shows {specific scenario}
- [ ] API reference includes {specific elements}
```

**Example:**
```markdown
**Acceptance Criteria:**
- [ ] batch_get_item example added to docs/tables.rst
- [ ] Example shows handling of unprocessed keys
- [ ] API reference documents parameters and return type
- [ ] Error handling example shows BatchOperationError
```

### Refactoring Criteria

Focus on measurable improvements:

```markdown
**Acceptance Criteria:**
- [ ] {Code} extracted into {location}
- [ ] {Duplicate code} consolidated into {shared location}
- [ ] All tests still pass (behavior unchanged)
- [ ] {Specific metric} reduced from {X} to {Y}
```

**Example:**
```markdown
**Acceptance Criteria:**
- [ ] Table validation logic extracted into TableValidator class
- [ ] Duplicate validation code removed from Application and TableClient
- [ ] All existing tests pass without modification
- [ ] Validation code reduced from 150 lines to 50 lines
```

## Common Mistakes

### Mistake 1: Subjective Quality Claims

❌ **Bad:**
```markdown
- [ ] Code is clean and maintainable
- [ ] Tests are comprehensive
- [ ] Documentation is clear
- [ ] Error handling is robust
```

✅ **Good:**
```markdown
- [ ] TableValidator class has single responsibility (validation only)
- [ ] Tests cover success case, ValueError, and TypeError scenarios
- [ ] Documentation includes method signature and usage example
- [ ] Error handling catches DynamoDBException and logs with context
```

### Mistake 2: Vague Functional Requirements

❌ **Bad:**
```markdown
- [ ] Batch operations work correctly
- [ ] Retry logic is implemented
- [ ] Errors are handled properly
```

✅ **Good:**
```markdown
- [ ] batch_get_item() retrieves all requested items when successful
- [ ] Failed items retried max 3 times with exponential backoff (1s, 2s, 4s)
- [ ] BatchOperationError raised with list of failed keys after retries exhausted
```

### Mistake 3: Implementation Details

❌ **Bad:**
```markdown
- [ ] Create BatchOperationHandler class
- [ ] Use @retry decorator on batch methods
- [ ] Store retry count in self._retry_count
- [ ] Implement _exponential_backoff() helper
```

✅ **Good:**
```markdown
- [ ] Failed batch items are retried automatically
- [ ] Retry wait time doubles after each attempt (exponential backoff)
- [ ] Maximum of 3 retry attempts before raising error
```

### Mistake 4: Repeating Project Standards

❌ **Bad:**
```markdown
- [ ] Tests achieve ≥90% coverage
- [ ] Code passes ./lint.sh with zero errors
- [ ] All functions have type hints
- [ ] All public APIs have docstrings
- [ ] No hardcoded values in implementation
- [ ] Code follows PEP 8 style guide
```

✅ **Good:**
```markdown
(Don't include these - they're already project standards)

Only include if there's something specific:
- [ ] Tests cover timeout edge case (0s, max 900s, over max 1000s)
- [ ] Docstring includes example of retry behavior
```

### Mistake 5: Ambiguous Scope

❌ **Bad:**
```markdown
- [ ] Documentation updated
- [ ] Examples added
- [ ] Tests improved
```

✅ **Good:**
```markdown
- [ ] batch_get_item example added to docs/tables.rst section "Batch Operations"
- [ ] Example shows error handling for BatchOperationError
- [ ] Tests cover partial failure scenario (some keys succeed, some fail)
```

## Validation Checklist

For each acceptance criterion, verify:

- [ ] Can be answered yes/no without subjective judgment
- [ ] Specific about what, where, or how much
- [ ] Focuses on behavior, not implementation (unless required)
- [ ] Not repeating project standards
- [ ] Measurable or verifiable through testing
- [ ] No subjective language (robust, clean, easy, etc.)
- [ ] Clear enough for someone else to verify

## Examples by Issue Type

### Example 1: Feature - Batch Operations

```markdown
**Acceptance Criteria:**
- [ ] TableClient.batch_get_item(keys: List[dict]) method implemented
- [ ] TableClient.batch_write_item(items: List[TableObject]) method implemented
- [ ] batch_get_item raises ValueError when keys exceed 100
- [ ] batch_write_item raises ValueError when items exceed 25
- [ ] Unprocessed items retried max 3 times
- [ ] Wait time doubles after each retry (1s, 2s, 4s)
- [ ] BatchOperationError raised when retries exhausted
- [ ] BatchOperationError includes list of failed keys/items
- [ ] Tests cover: success, partial failure, total failure, oversized batch
- [ ] CHANGELOG.md entry added under "Unreleased" section
```

### Example 2: Bug - Lambda Timeout

```markdown
**Acceptance Criteria:**
- [ ] Lambda timeout reads settings.lambda_timeout value
- [ ] Lambda timeout defaults to 30 seconds when not set
- [ ] Lambda timeout raises ValueError when exceeds 900 seconds
- [ ] CDK synthesized template shows correct timeout value
- [ ] Test verifies timeout with configured value
- [ ] Test verifies timeout with default value
- [ ] Test verifies timeout validation for invalid values
- [ ] CHANGELOG.md entry added under "Unreleased" section
```

### Example 3: Task - Documentation

```markdown
**Acceptance Criteria:**
- [ ] New section "Batch Operations" added to docs/tables.rst
- [ ] Section includes batch_get_item usage example
- [ ] Section includes batch_write_item usage example
- [ ] Example shows error handling for BatchOperationError
- [ ] Example shows handling oversized batch (>100 items)
- [ ] API reference updated with batch method signatures
- [ ] API reference documents BatchOperationError exception
```

### Example 4: Refactoring - Extract Validator

```markdown
**Acceptance Criteria:**
- [ ] TableValidator class created in da_vinci/core/orm/validator.py
- [ ] validate_table_definition() static method implemented
- [ ] Application uses TableValidator.validate_table_definition()
- [ ] TableClient uses TableValidator.validate_table_definition()
- [ ] Duplicate validation code removed from Application
- [ ] Duplicate validation code removed from TableClient
- [ ] All existing tests pass without modification
- [ ] Validator logic unchanged (only location changed)
```

## Anti-Patterns to Avoid

### 1. Too Many Criteria
If you have more than 10 criteria, consider:
- Breaking into multiple issues
- Removing redundant criteria
- Removing criteria that are project standards

### 2. Too Few Criteria
If you have fewer than 3 criteria:
- Are requirements specific enough?
- Are edge cases covered?
- Is documentation/CHANGELOG included?

### 3. Mix of Functional and Quality Criteria
Keep separate if needed:

```markdown
**Functional Criteria:**
- [ ] batch_get_item() method implemented
- [ ] Method handles up to 100 items
- [ ] Unprocessed items retried

**Testing Criteria:**
- [ ] Tests cover success, failure, and partial failure cases
- [ ] Tests verify retry behavior with mock delay

**Documentation Criteria:**
- [ ] Usage example added to docs/tables.rst
- [ ] CHANGELOG.md updated
```

### 4. Open-Ended Criteria

❌ **Bad:** "Add examples"
✅ **Good:** "Add batch_get_item example to docs/tables.rst showing error handling"

❌ **Bad:** "Improve tests"
✅ **Good:** "Add tests for retry behavior with mocked exponential backoff timing"

## Quick Reference

| ❌ Avoid | ✅ Use Instead |
|---------|---------------|
| "Code is clean" | "TableValidator has single responsibility" |
| "Tests are comprehensive" | "Tests cover success, ValueError, and TypeError" |
| "Error handling is robust" | "DynamoDBException caught and logged with context" |
| "API is easy to use" | "API provides get(), put(), delete() methods" |
| "Documentation is clear" | "Documentation includes parameters, return type, and example" |
| "Tests have good coverage" | (omit - project standard) |
| "Code follows style guide" | (omit - enforced by ./lint.sh) |
| "Implementation is efficient" | "Reduces API calls from 10 to 1" |
| "Works correctly" | "Returns expected output for valid input" |
| "Handles errors well" | "Raises ValueError for invalid input" |
