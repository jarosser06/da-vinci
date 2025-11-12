# Coverage Requirements

Test coverage thresholds and reporting for da_vinci.

## Coverage Threshold

- **Minimum**: 90% coverage required
- **Scope**: Combined coverage across both packages
- **Enforcement**: Checked before PR approval

## Running Coverage

- `./test.sh --coverage` - Generate coverage report
- HTML report: `htmlcov/index.html`
- Terminal output: Shows missing lines

## Coverage Configuration

All coverage configuration in root `pyproject.toml`:
- Source paths: da_vinci and da_vinci_cdk
- Omit patterns: tests, __pycache__, site-packages
- Exclude lines: pragma no cover, abstractmethod, TYPE_CHECKING

## Excluded from Coverage

- Test files themselves
- Abstract methods
- Type checking blocks
- Defensive assertions
- Debug/repr methods

## Best Practices

- Test the happy path first
- Add error condition tests
- Don't test framework internals
- Focus on business logic coverage
- Use coverage report to find gaps
