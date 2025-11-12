# Lambda Patterns

Best practices for Lambda functions in the Da Vinci framework.

## Handler Design

### Keep Handlers Thin
- Minimal logic in handler function
- Delegate to service layer
- Handler only for AWS event processing

### Error Handling
- Let exceptions propagate
- Report to exception trap if enabled
- Include context in errors

## Docker-Based Deployment

### Library Base Image
- Contains framework code and dependencies
- Shared across Lambda functions
- Managed by Application class

### Application Image
- Contains application code
- Built on top of library base image
- Customizable via Dockerfile

## Resource Access

### Service Discovery
- Use resource discovery to find ARNs
- Avoid hardcoded resource identifiers
- Environment-aware lookups

## Best Practices

- Keep cold start time minimal
- Centralize business logic in service layer
