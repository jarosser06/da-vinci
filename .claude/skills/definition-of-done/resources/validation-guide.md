# Issue Validation Guide

This guide helps you validate that completed work meets all issue requirements and acceptance criteria.

## Validation Process

### 1. Fetch and Parse Issue Details

Always start by fetching the full issue from GitHub:
- Use the github-operations skill to get issue details
- Extract all requirements from the description
- Identify acceptance criteria (often in checklists or "Acceptance Criteria" sections)
- Note any edge cases or constraints mentioned

### 1a. Validate Issue Quality (Optional)

If the issue contains subjective language or unclear requirements:
- Flag subjective adverbs: "easily", "simply", "quickly"
- Flag subjective adjectives: "powerful", "robust", "elegant"
- Flag vague requirements: "improve", "enhance" (without specifics)
- Flag ambiguous acceptance criteria that aren't yes/no verifiable
- Note: This is informational - proceed with validation based on interpretation

### 2. Map Requirements to Implementation

For each requirement:
- Identify the specific code changes that address it
- List the files modified for this requirement
- Note the relevant functions/classes/modules

### 3. Verify Implementation Completeness

Check that:
- All requirements have corresponding implementation
- No requirements were partially implemented
- Edge cases mentioned in the issue are handled
- Any specific constraints or conditions are met

### 4. Validate Test Coverage

For each requirement:
- Identify tests that validate the requirement
- Check that tests cover happy path and edge cases
- Verify test assertions validate behavior, not just existence
- Confirm overall coverage is ≥90%

### 5. Check Quality Gates

Automated checks:
- `./test.sh` passes all tests
- `./lint.sh` passes with zero errors
- Coverage meets 90% threshold

Manual checks:
- Code follows project standards
- No hardcoded values or credentials
- Error handling is appropriate
- Logging is informative

### 6. Verify Documentation

Check if documentation updates are needed:
- User-facing changes require documentation updates
- API changes need docstring updates
- Breaking changes need CHANGELOG.md entries
- New features may need examples or guides

### 7. CHANGELOG.md

Verify CHANGELOG.md is updated:
- Entry added under "Unreleased" section
- Entry describes user-facing changes
- Entry follows format: `- [Added/Changed/Fixed/Removed] description`

## Common Issue Patterns

### Feature Request

Requirements typically include:
- Functional requirements (what it should do)
- API surface (new functions/classes)
- Integration points (how it connects)
- Examples (how users will use it)

Validation checklist:
- ✅ All functional requirements implemented
- ✅ API matches specification
- ✅ Integration points working
- ✅ Examples provided (in tests or docs)

### Bug Fix

Requirements typically include:
- Bug description (what's wrong)
- Expected behavior (what should happen)
- Current behavior (what actually happens)
- Steps to reproduce

Validation checklist:
- ✅ Bug no longer occurs
- ✅ Expected behavior achieved
- ✅ Regression test added
- ✅ Root cause addressed (not just symptom)

### Documentation

Requirements typically include:
- What needs documenting
- Target audience
- Level of detail
- Examples or diagrams

Validation checklist:
- ✅ All topics covered
- ✅ Appropriate detail level
- ✅ Examples provided
- ✅ Accuracy verified

### Refactoring

Requirements typically include:
- What to refactor
- Why (improve readability, reduce complexity, etc.)
- Any behavior changes (usually none)

Validation checklist:
- ✅ Refactoring complete
- ✅ Behavior unchanged (tests still pass)
- ✅ Code quality improved
- ✅ No new bugs introduced

## Acceptance Criteria Patterns

### Checklist Format

```markdown
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3
```

Validation: Each checkbox item must be verifiable in the implementation.

### Scenario Format

```markdown
**Acceptance Criteria:**
- Given X, when Y, then Z
- Given A, when B, then C
```

Validation: Each scenario should have a corresponding test case.

### Explicit List

```markdown
**Acceptance Criteria:**
1. Feature A must support X
2. Feature B must handle Y
3. Error Z must be caught and logged
```

Validation: Each numbered item must be implemented and tested.

## Red Flags

Watch for these warning signs:

### Issue Quality Issues
- Subjective language in requirements ("easily add", "robust handling")
- Vague acceptance criteria ("tests should be comprehensive")
- Ambiguous requirements without specifics ("improve performance")
- Note: These are informational - interpret requirements objectively

### Incomplete Implementation
- Requirements mentioned but no code changes for them
- Partial implementation with TODOs
- Features disabled or commented out

### Missing Tests
- New functions/classes without tests
- Edge cases not tested
- Only happy path tested

### Quality Issues
- Linting errors present
- Test coverage below 90%
- Tests failing or skipped

### Documentation Gaps
- CHANGELOG.md not updated
- API changes without docstring updates
- User-facing changes not documented

## Examples

### Example 1: Feature Implementation

**Issue Requirements:**
- Add support for batch operations in DynamoDB ORM
- Support batch_get_item for up to 100 items
- Support batch_write_item for up to 25 items
- Handle unprocessed items with retry logic

**Validation:**
```markdown
✅ batch_get_item method implemented in ORM class
✅ Supports up to 100 items (validated in tests)
✅ batch_write_item method implemented
✅ Supports up to 25 items (validated in tests)
✅ Retry logic for unprocessed items implemented
✅ Tests cover all batch sizes and retry scenarios
✅ CHANGELOG.md updated with new feature
```

### Example 2: Bug Fix

**Issue Requirements:**
- Fix Lambda timeout not being applied from settings
- Default should be 30 seconds if not specified
- Settings value should override default

**Validation:**
```markdown
✅ Lambda timeout now reads from settings
✅ Default of 30 seconds applied when not specified
✅ Settings value correctly overrides default
✅ Regression test added for timeout configuration
✅ Existing tests still pass
✅ CHANGELOG.md updated with bug fix
```

## Tips

1. **Be thorough**: Don't assume requirements are met without verification
2. **Check edge cases**: Issues often mention edge cases that are easy to forget
3. **Verify tests**: Coverage percentage doesn't mean requirements are tested
4. **Read carefully**: Requirements may be embedded in issue description prose
5. **Ask questions**: If a requirement is unclear, validate your interpretation
