# Pytest Basics

Pytest configuration and test organization for da_vinci.

## Test Discovery

### File Naming
- Test files: `test_*.py` or `*_test.py`
- Test classes: Prefix with `Test`
- Test functions: Prefix with `test_`

### Test Locations
- Core package tests: `da_vinci/tests/`
- CDK package tests: `da_vinci-cdk/tests/`

## Configuration

All pytest configuration is in root `pyproject.toml`:
- Test paths configured
- Coverage settings defined
- Markers registered (unit, integration, slow)

## Test Organization

### Test Classes
- Group related tests in classes
- Use descriptive class names
- One class per module or feature being tested

### Test Functions
- Descriptive names that explain what is tested
- One assertion concept per test
- Clear arrange-act-assert structure

## Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
