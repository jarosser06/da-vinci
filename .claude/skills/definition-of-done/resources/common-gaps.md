# Common Gaps in Completed Work

This guide lists common things developers forget when completing issues.

## Documentation Gaps

### CHANGELOG.md Not Updated
**Symptom**: Changes made but CHANGELOG.md unchanged
**Fix**: Add entry under "Unreleased" section following format:
```markdown
## [Unreleased]

### Added
- Feature description

### Changed
- Modification description

### Fixed
- Bug fix description
```

### Missing Docstrings
**Symptom**: New public functions/classes without docstrings
**Fix**: Add comprehensive docstrings:
```python
def new_function(param: str) -> bool:
    """
    Brief description of what function does.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When validation fails
    """
```

### Outdated Documentation
**Symptom**: API changes not reflected in docs
**Fix**: Update relevant documentation files in `docs/` directory

### Missing Type Hints
**Symptom**: Functions without proper type annotations
**Fix**: Add type hints to all parameters and return values

## Test Coverage Gaps

### Happy Path Only
**Symptom**: Tests only cover successful scenarios
**Fix**: Add tests for:
- Error conditions
- Edge cases (empty lists, None values, boundary conditions)
- Invalid inputs
- Retry/timeout scenarios

### Missing Integration Tests
**Symptom**: Unit tests exist but integration scenarios untested
**Fix**: Add tests that verify components work together

### Weak Assertions
**Symptom**: Tests check existence but not behavior
```python
# Bad
def test_process():
    result = process_data(data)
    assert result is not None  # Too weak!

# Good
def test_process():
    result = process_data(data)
    assert result == expected_output
    assert result.status == "completed"
```

### Mocking Everything
**Symptom**: Over-mocking hides integration issues
**Fix**: Balance mocking - mock external services, test internal logic

### Coverage vs Quality
**Symptom**: 90% coverage but requirements not validated
**Fix**: Ensure tests actually validate requirements, not just execute code

## Implementation Gaps

### Partial Requirements
**Symptom**: Some requirements met, others ignored
**Fix**: Go through each requirement systematically and implement all of them

### Edge Cases Ignored
**Symptom**: Issue mentions edge cases but they're not handled
**Fix**:
- Re-read issue for mentioned edge cases
- Add handling for each case
- Add tests for each edge case

### Error Handling Missing
**Symptom**: No error handling for failure scenarios
**Fix**: Add appropriate error handling:
```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise
```

### Hardcoded Values
**Symptom**: Configuration values hardcoded in implementation
**Fix**: Use settings or constants:
```python
# Bad
timeout = 300

# Good
timeout = settings.lambda_timeout
```

## Quality Gate Gaps

### Linting Errors
**Symptom**: `./lint.sh` shows errors
**Fix**: Run `./lint.sh --fix` and fix remaining issues

### Failing Tests
**Symptom**: `./test.sh` has failures
**Fix**: Fix all test failures before completing issue

### Low Coverage
**Symptom**: Coverage below 90%
**Fix**: Add tests for uncovered code paths

## Process Gaps

### Not Assigned to Issue
**Symptom**: Working on issue but not assigned
**Fix**: Assign yourself to the issue:
```bash
gh api user --jq .login
# Then update issue with your username
```

### Wrong Branch Name
**Symptom**: Branch doesn't follow convention
**Fix**: Use format: `issue/<#>`

### Messy Commit History
**Symptom**: Many "fix typo" or "wip" commits
**Fix**: Squash commits into logical units before PR

## Requirement Interpretation Gaps

### Assumed Requirements
**Symptom**: Implementation includes features not requested
**Fix**: Only implement what's explicitly requested or clearly implied

### Scope Creep
**Symptom**: Added "nice to have" features beyond issue scope
**Fix**: Stick to issue requirements; create new issues for additional ideas

### Misunderstood Requirements
**Symptom**: Implementation doesn't match intent
**Fix**: Re-read issue carefully; ask for clarification if unclear

## Common "Gotchas"

### 1. Not Using Project Scripts
**Problem**: Running pytest/flake8 directly instead of `./test.sh` and `./lint.sh`
**Impact**: May miss configuration or environment setup
**Fix**: Always use project scripts

### 2. Testing Against Wrong Data
**Problem**: Tests use simplified data that doesn't match production
**Impact**: Tests pass but code fails in production
**Fix**: Use realistic test data including edge cases

### 3. Not Testing Backwards Compatibility
**Problem**: Changes break existing usage
**Impact**: Breaking changes without major version bump
**Fix**: Test that existing code still works

### 4. Forgetting Type Checking
**Problem**: No type hints or mypy errors ignored
**Impact**: Type errors caught late
**Fix**: Add type hints; run `./lint.sh` which includes mypy

### 5. Not Reading Related Code
**Problem**: Duplicating existing functionality
**Impact**: Code inconsistency and duplication
**Fix**: Search for similar patterns before implementing

## Checklist for Self-Review

Before marking work complete, verify:

- [ ] All issue requirements implemented
- [ ] All acceptance criteria met
- [ ] Tests added for new code (≥90% coverage)
- [ ] Tests validate behavior, not just coverage
- [ ] Edge cases mentioned in issue handled
- [ ] `./test.sh` passes
- [ ] `./lint.sh` passes
- [ ] CHANGELOG.md updated
- [ ] Docstrings added for public APIs
- [ ] Type hints on all functions
- [ ] No hardcoded values
- [ ] Error handling appropriate
- [ ] Documentation updated if needed
- [ ] Assigned to issue in GitHub
- [ ] Branch name follows convention
- [ ] Commits are clean and logical

## When to Ask for Help

If you encounter:
- Unclear requirements
- Technical blockers
- Scope questions (should this be included?)
- Test strategy uncertainty
- Architecture decisions

Don't guess - ask the user or create a follow-up issue!
