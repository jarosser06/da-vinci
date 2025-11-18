# Code Review Checklist

Comprehensive checklist for reviewing da_vinci code changes.

## Code Quality

- [ ] Follows PEP 8 style guidelines
- [ ] 100 character line length respected
- [ ] Double quotes used for strings
- [ ] Type hints on all public APIs
- [ ] Docstrings on public functions and classes
- [ ] No unused imports
- [ ] No commented-out code

## Architecture

- [ ] Code is in the right package (core vs CDK)
- [ ] Follows existing patterns in the module
- [ ] Table definitions centralized
- [ ] Stack dependencies explicit
- [ ] No circular dependencies

## Error Handling

- [ ] Exceptions have meaningful messages
- [ ] Error context included
- [ ] No bare except clauses
- [ ] Proper exception types used

## Testing

### Coverage Quality (Not Just Quantity)
- [ ] Tests cover new code (≥90% coverage threshold)
- [ ] Test names are descriptive and explain what is being tested
- [ ] Tests validate behavior, not just instantiation
- [ ] Mocks used appropriately for AWS services and external dependencies

### Edge Cases & Scenarios
- [ ] **Different parameter combinations tested**:
  - Required parameters only
  - Optional parameters with various values
  - Default values vs. custom values
  - Multiple valid configurations
- [ ] **Edge cases covered**:
  - Boundary conditions (min/max values, empty strings, zero values)
  - Invalid inputs and error handling
  - Null/None values where applicable
  - Empty collections vs. populated collections
- [ ] **State transitions tested** (if applicable):
  - Object lifecycle (creation → modification → deletion)
  - Different execution paths through the code
- [ ] **Integration scenarios**:
  - Interaction with other constructs/components
  - Dependencies and relationships
  - Cross-stack references (for CDK)

### Test Structure & Quality
- [ ] Tests use shared fixtures from conftest.py (CDK tests)
- [ ] Tests are isolated and don't depend on execution order
- [ ] Setup and teardown handled properly
- [ ] Test data is realistic and meaningful
- [ ] Assertions validate expected outcomes, not just existence
- [ ] Tests fail for the right reasons (validate test correctness)

### CDK-Specific Testing (when applicable)
- [ ] Template synthesis validated with `Template.from_stack()`
- [ ] Resource counts verified with `resource_count_is()`
- [ ] Resource properties validated with `has_resource_properties()`
- [ ] Correct resource types used (e.g., GlobalTable vs. Table)
- [ ] Custom resources properly typed (Custom::DaVinci@*)
- [ ] IAM permissions and grants tested
- [ ] Context values properly provided
- [ ] Docker builds mocked or fixtures used appropriately

### Test Coverage Gaps to Avoid
- [ ] **Not testing different options**: If a function accepts optional parameters, test with/without them
- [ ] **Not testing error paths**: Ensure exceptions and error conditions are tested
- [ ] **Testing only happy path**: Include failure scenarios and edge cases
- [ ] **Shallow assertions**: Don't just check `is not None`, verify actual behavior
- [ ] **Missing parameter combinations**: Test all significant combinations of parameters
- [ ] **Ignoring conditional logic**: All branches (if/else) should be exercised
- [ ] **Skipping integration**: Test how components work together, not just in isolation

## Documentation

- [ ] Docstrings explain why, not just what
- [ ] Breaking changes clearly marked if applicable

## Git

- [ ] Commits squashed appropriately
- [ ] Commit messages follow format
- [ ] Branch name is descriptive
- [ ] No merge conflicts
