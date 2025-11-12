# Common Issues

Common problems to watch for in da_vinci code reviews.

## Python Anti-Patterns

### String Quotes
- Using single quotes instead of double quotes
- Inconsistent quote usage

### Import Organization
- Imports not organized (stdlib, third-party, local)
- Unused imports
- Wildcard imports

### Type Hints
- Missing type hints on public APIs
- Incorrect type annotations
- Using Any when specific type is known

## Da Vinci-Specific Issues

### Table Definitions
- Tables defined in multiple places
- Inconsistent table naming
- Missing table definitions

### Stack Dependencies
- Implicit dependencies between stacks
- Circular stack dependencies
- Missing dependency declarations

### Resource Access
- Hardcoded ARNs or resource names
- Not using service discovery
- Hardcoded environment values

## Testing Issues

### Coverage
- New code not tested
- Only happy path tested
- Missing edge case tests

### Mocking
- Not mocking AWS services
- Mocking internal framework code
- Overly complex mocks

### Test Organization
- Tests in wrong location
- Unclear test names
- Multiple assertions per test

## Performance Issues

### Lambda Cold Start
- Heavy imports at module level
- Unnecessary dependencies loaded
- Large Docker images

### DynamoDB Access
- N+1 query patterns
- Not using batch operations
- Missing indexes
