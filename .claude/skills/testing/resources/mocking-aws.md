# Mocking AWS Services

Patterns for mocking AWS services in tests.

## Tools

### pytest-mock
- Built-in mock fixtures
- Simpler syntax than unittest.mock
- Automatic cleanup

### boto3-stubs
- Type hints for boto3
- Better IDE support
- Installed in dev dependencies

## Mocking Strategies

### Mock boto3 Clients
- Mock at the boto3.client level
- Return mock responses
- Avoid hitting real AWS

### Mock DynamoDB
- Mock table operations
- Test ORM behavior
- Verify calls without real tables

### Mock Lambda Invocations
- Mock lambda client
- Test event handling
- Verify payloads

## Best Practices

- Mock at the boundary (boto3 clients)
- Use realistic response structures
- Test error conditions
- Verify AWS calls were made correctly
- Don't mock internal framework code
