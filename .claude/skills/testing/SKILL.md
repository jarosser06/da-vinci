# Testing

**Description**: Run tests and manage test coverage for da_vinci packages. Use when executing tests or checking test results.

## When to Use This Skill

- Running tests for core or CDK packages
- Checking test coverage
- Validating test results before PR
- Orchestrating test execution

## Quick Reference

### Test Commands
- `./test.sh` - Run all tests (both packages)
- `./test.sh core` - Test da_vinci core only
- `./test.sh cdk` - Test da_vinci-cdk only
- `./test.sh --coverage` - Run with coverage report

### Test Structure
- Core tests: `da_vinci/tests/`
- CDK tests: `da_vinci-cdk/tests/`
- Framework: pytest
- Coverage tool: pytest-cov

## Resource Guides

### 📖 [Pytest Basics](resources/pytest-basics.md)
Pytest configuration and test organization.

**Use when**: Understanding test structure or pytest settings.

### 📖 [Mocking AWS](resources/mocking-aws.md)
Patterns for mocking AWS services in tests.

**Use when**: Writing tests that interact with AWS services.

### 📖 [Coverage Requirements](resources/coverage.md)
Coverage thresholds and reporting.

**Use when**: Checking if coverage meets requirements.

## Key Principles

1. **90% Coverage Minimum**: Required for PR approval
2. **Test Both Packages**: Run both core and CDK tests before PR
3. **Use Mocks for AWS**: Don't hit real AWS services in tests
4. **Keep Tests Fast**: Avoid slow integration tests where possible
