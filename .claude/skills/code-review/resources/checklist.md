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

- [ ] Tests cover new code
- [ ] Test names are descriptive
- [ ] Mocks used for AWS services
- [ ] Edge cases tested
- [ ] Coverage meets 90% threshold

## Documentation

- [ ] Docstrings explain why, not just what
- [ ] Breaking changes clearly marked if applicable

## Git

- [ ] Commits squashed appropriately
- [ ] Commit messages follow format
- [ ] Branch name is descriptive
- [ ] No merge conflicts
