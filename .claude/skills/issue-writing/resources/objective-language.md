# Objective Language in GitHub Issues

GitHub issues should be clear, factual, and objective. Avoid subjective language, marketing terms, and vague requirements.

## Why Objective Language Matters

**Issues are specifications, not sales pitches**
- Developers need clear, actionable requirements
- Acceptance criteria must be verifiable
- Subjective language creates ambiguity
- Objective language enables accurate estimation

**Objective language prevents misunderstandings**
- Requirements are unambiguous
- Success criteria are measurable
- Implementation expectations are clear
- Review criteria are well-defined

## Categories of Subjective Language to Avoid

### 1. Subjective Adverbs

Avoid words that make claims about ease, speed, or quality:

❌ **Avoid**: easily, simply, quickly, obviously, clearly, straightforwardly, effortlessly, seamlessly

**Examples**

❌ **Bad**: "Easily add support for batch operations"
✅ **Good**: "Add support for batch operations with batch_get_item and batch_write_item methods"

❌ **Bad**: "Simply update the Lambda timeout configuration"
✅ **Good**: "Update Lambda timeout to read from settings with 30-second default"

❌ **Bad**: "Quickly implement error handling"
✅ **Good**: "Implement error handling for DynamoDB service exceptions"

### 2. Subjective Adjectives

Avoid words that express opinions about quality:

❌ **Avoid**: powerful, elegant, beautiful, amazing, excellent, great, robust, clean, nice

**Examples**

❌ **Bad**: "Create a robust error handling system"
✅ **Good**: "Create error handling that catches DynamoDB exceptions and logs with context"

❌ **Bad**: "Implement a clean API for table operations"
✅ **Good**: "Implement API with methods: get(), put(), delete(), scan(), query()"

❌ **Bad**: "Add an elegant solution for retries"
✅ **Good**: "Add exponential backoff retry logic with max 3 attempts"

### 3. Vague Requirements

Requirements must be specific and measurable:

❌ **Avoid**: "improve", "enhance", "better", "optimize", "refactor" (without specifics)

**Examples**

❌ **Bad**: "Improve test coverage"
✅ **Good**: "Add tests for error conditions in TableClient.query() method"

❌ **Bad**: "Enhance the documentation"
✅ **Good**: "Add code examples for batch operations to docs/tables.rst"

❌ **Bad**: "Optimize Lambda performance"
✅ **Good**: "Reduce Lambda cold start time by lazy-loading boto3 clients"

❌ **Bad**: "Refactor the ORM module"
✅ **Good**: "Extract table schema validation into separate TableValidator class"

### 4. Ambiguous Acceptance Criteria

Acceptance criteria must be verifiable with yes/no answers:

❌ **Bad**: "Code should be clean and maintainable"
✅ **Good**: "Code passes ./lint.sh with zero errors"

❌ **Bad**: "Tests should be comprehensive"
✅ **Good**: "Tests cover success case, error case, and empty input case for each new method"

❌ **Bad**: "Documentation should be clear"
✅ **Good**: "Documentation includes: method signature, parameters, return value, and usage example"

### 5. Assumptions About Difficulty

Don't make assumptions about how hard something is:

❌ **Avoid**: "This should be easy", "Quick fix", "Trivial change", "Simple task"

**Examples**

❌ **Bad**: "This should be a quick fix for the timeout bug"
✅ **Good**: "Fix Lambda timeout not reading from settings"

❌ **Bad**: "Simple refactoring to extract common code"
✅ **Good**: "Extract duplicate table validation logic into shared validate_table_definition() function"

### 6. Implementation Opinions

Don't dictate implementation unless necessary:

❌ **Bad**: "Use the elegant builder pattern for this"
✅ **Good**: "Create fluent API for query construction" (if pattern is truly required)
✅ **Better**: "Add support for chaining query conditions" (describe requirement, not pattern)

❌ **Bad**: "Make this more Pythonic"
✅ **Good**: "Replace dict access with dataclass attributes for type safety"

## Writing Clear Requirements

### Feature Requirements

**Template:**
```markdown
Add [specific functionality] that [does what].

Functionality:
- [Specific behavior 1]
- [Specific behavior 2]
- [Specific behavior 3]

API:
- [Method/class names if specified]
- [Parameters if specified]
- [Return values if specified]
```

**Example:**
```markdown
Add batch operation support for DynamoDB table client.

Functionality:
- batch_get_item() retrieves multiple items (up to 100) in single request
- batch_write_item() writes multiple items (up to 25) in single request
- Handle unprocessed items with retry logic (max 3 attempts)
- Raise BatchOperationError when all retries exhausted

API:
- TableClient.batch_get_item(keys: List[dict]) -> List[TableObject]
- TableClient.batch_write_item(items: List[TableObject]) -> None
```

### Bug Requirements

**Template:**
```markdown
Fix [specific problem].

Current Behavior:
- [What currently happens]

Expected Behavior:
- [What should happen]

Steps to Reproduce:
1. [Step 1]
2. [Step 2]
3. [Step 3]
```

**Example:**
```markdown
Fix Lambda timeout not reading from settings.

Current Behavior:
- Lambda functions always use 30-second timeout
- settings.lambda_timeout value is ignored

Expected Behavior:
- Lambda functions use settings.lambda_timeout value
- Default to 30 seconds if settings.lambda_timeout not set

Steps to Reproduce:
1. Set settings.lambda_timeout = 300
2. Deploy Lambda function
3. Check Lambda configuration - shows 30 seconds, not 300
```

### Task Requirements

**Template:**
```markdown
[Action] [specific target].

Items to Complete:
- [ ] [Specific item 1]
- [ ] [Specific item 2]
- [ ] [Specific item 3]

Context:
[Why this is needed, background information]
```

**Example:**
```markdown
Update documentation with batch operation examples.

Items to Complete:
- [ ] Add batch_get_item example to docs/tables.rst
- [ ] Add batch_write_item example to docs/tables.rst
- [ ] Add error handling example for batch operations
- [ ] Update API reference with batch method signatures

Context:
Batch operations were added in #123 but documentation was not updated.
```

## Writing Verifiable Acceptance Criteria

### Functional Criteria

Each criterion should be testable with yes/no answer:

✅ **Good Functional Criteria:**
```markdown
- [ ] batch_get_item() method exists on TableClient
- [ ] batch_get_item() accepts List[dict] parameter
- [ ] batch_get_item() returns List[TableObject]
- [ ] batch_get_item() handles up to 100 items
- [ ] Unprocessed items are retried (max 3 attempts)
- [ ] BatchOperationError raised when retries exhausted
```

❌ **Bad Functional Criteria:**
```markdown
- [ ] Batch operations work well
- [ ] Error handling is robust
- [ ] API is easy to use
- [ ] Implementation is efficient
```

### Quality Criteria

Quality criteria should reference existing standards:

✅ **Good Quality Criteria:**
```markdown
- [ ] Tests pass (./test.sh)
- [ ] Linting passes (./lint.sh)
- [ ] Coverage ≥90% (enforced by project)
- [ ] Type hints on all public methods
- [ ] Docstrings on all public methods
- [ ] CHANGELOG.md updated
```

❌ **Don't include obvious quality criteria:**
```markdown
- [ ] Code follows PEP 8 (already enforced by ./lint.sh)
- [ ] Tests have good assertions (covered by testing standards)
- [ ] No hardcoded values (covered by code review standards)
```

These are project standards and don't need to be repeated in every issue.

### Documentation Criteria

Be specific about what documentation is needed:

✅ **Good Documentation Criteria:**
```markdown
- [ ] Add usage example to docs/tables.rst
- [ ] Update API reference with new methods
- [ ] Add CHANGELOG.md entry under "Unreleased"
```

❌ **Bad Documentation Criteria:**
```markdown
- [ ] Documentation is updated
- [ ] Examples are clear
- [ ] API is well documented
```

## What NOT to Include in Issues

### Don't Include Project Standards

These are already defined in project documentation:

❌ **Don't repeat:**
- "Tests must have ≥90% coverage" (project standard)
- "Code must pass linting" (enforced by ./lint.sh)
- "Follow PEP 8" (enforced by ./lint.sh)
- "Add type hints" (code review standard)
- "Add docstrings" (code review standard)
- "No hardcoded values" (code review standard)

✅ **Only include if there's something specific:**
- "Tests must cover timeout scenarios" (specific to this issue)
- "Add example to docs/tables.rst" (specific documentation requirement)

### Don't Include Implementation Details (Usually)

Let developers choose implementation unless there's a specific reason:

❌ **Too prescriptive:**
```markdown
Create a RetryHandler class with exponential_backoff() method.
Use decorator pattern to wrap existing methods.
Store retry state in instance variable.
```

✅ **Better:**
```markdown
Add retry logic for DynamoDB throttling errors.
- Max 3 retry attempts
- Exponential backoff (1s, 2s, 4s)
- Raise ThrottlingError when retries exhausted
```

### Don't Include Motivational Language

Issues are specifications, not pep talks:

❌ **Avoid:**
- "This will make Da Vinci even better!"
- "Users will love this feature"
- "This is an exciting enhancement"
- "Let's improve the developer experience"

✅ **Instead, state context factually:**
- "Current API requires separate calls for each item"
- "boto3 supports batch operations that reduce API calls"

## Examples

### Example 1: Good Feature Issue

```markdown
**Title:** Add batch operations to TableClient

**Description:**
Add batch_get_item and batch_write_item methods to TableClient for retrieving and writing multiple DynamoDB items in single requests.

**Functionality:**
- batch_get_item() retrieves multiple items (up to 100)
- batch_write_item() writes multiple items (up to 25)
- Retry unprocessed items (max 3 attempts with exponential backoff)
- Raise BatchOperationError when retries exhausted

**API:**
- TableClient.batch_get_item(keys: List[dict]) -> List[TableObject]
- TableClient.batch_write_item(items: List[TableObject]) -> None

**Acceptance Criteria:**
- [ ] batch_get_item() method implemented
- [ ] batch_write_item() method implemented
- [ ] Methods handle AWS batch size limits (100/25)
- [ ] Unprocessed items retried with exponential backoff
- [ ] BatchOperationError raised after max retries
- [ ] Tests cover success, partial failure, and total failure
- [ ] CHANGELOG.md updated

**Context:**
boto3 DynamoDB batch operations reduce API calls for bulk operations. Current TableClient requires separate get/put calls for each item.

**Labels:** feature, priority: medium, package: core
```

### Example 2: Good Bug Issue

```markdown
**Title:** Lambda timeout ignores settings.lambda_timeout value

**Description:**
Lambda functions are deployed with 30-second timeout regardless of settings.lambda_timeout value.

**Steps to Reproduce:**
1. Set settings.lambda_timeout = 300 in settings
2. Deploy Lambda function with CDK
3. Check Lambda configuration in AWS Console
4. Timeout shows 30 seconds, not 300

**Expected Behavior:**
- Lambda uses settings.lambda_timeout value when set
- Lambda uses 30 seconds default when settings.lambda_timeout not set

**Current Behavior:**
- Lambda always uses 30 seconds
- settings.lambda_timeout is ignored

**Acceptance Criteria:**
- [ ] Lambda timeout reads from settings.lambda_timeout
- [ ] Default is 30 seconds when not set
- [ ] Deployed Lambda shows correct timeout value
- [ ] Test validates timeout configuration
- [ ] CHANGELOG.md updated

**Labels:** bug, priority: high, package: cdk
```

### Example 3: Good Task Issue

```markdown
**Title:** Add batch operations documentation

**Description:**
Add documentation and examples for batch_get_item and batch_write_item methods added in #123.

**Items to Complete:**
- [ ] Add batch_get_item example to docs/tables.rst
- [ ] Add batch_write_item example to docs/tables.rst
- [ ] Add error handling example for BatchOperationError
- [ ] Update API reference section with method signatures
- [ ] Add note about AWS batch size limits (100/25)

**Context:**
Batch operations were implemented in #123 but documentation was deferred to separate task.

**Labels:** task, priority: medium, package: core
```

## Checklist for Issue Writing

Before creating an issue, verify:

- [ ] Title clearly states what needs to be done
- [ ] Description is specific and factual
- [ ] No subjective language (easily, simply, robust, etc.)
- [ ] Requirements are measurable and verifiable
- [ ] Acceptance criteria are yes/no checkboxes
- [ ] No repeated project standards (test coverage, linting, etc.)
- [ ] Context explains why, not how great it will be
- [ ] Appropriate labels added (type, priority, package)
- [ ] Implementation details only included if required

## Quick Reference: Word Replacements

| ❌ Avoid | ✅ Use Instead |
|---------|---------------|
| "Easily add..." | "Add..." |
| "Simply update..." | "Update..." |
| "Robust error handling" | "Error handling for [specific errors]" |
| "Clean API" | "API with methods: [list methods]" |
| "Improve performance" | "Reduce [metric] from X to Y" |
| "Better testing" | "Add tests for [specific scenarios]" |
| "Enhance documentation" | "Add [specific content] to [specific file]" |
| "Make more maintainable" | "Extract [specific code] into [specific structure]" |
| "Should be easy" | (remove entirely) |
| "Quick fix" | (describe the fix) |
