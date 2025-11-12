# Da Vinci CDK Package

Contributing to the da_vinci-cdk package.

## Package Structure

### Constructs (da_vinci_cdk.constructs)
- Reusable CDK constructs
- Lambda function constructs
- DynamoDB table constructs
- S3 bucket constructs
- Other AWS resource wrappers

### Framework Stacks (da_vinci_cdk.framework_stacks)
- Pre-built infrastructure stacks
- Service stacks (event_bus, exceptions_trap)
- Table stacks
- Integration patterns

### Application (da_vinci_cdk.application)
- Main Application class
- Stack orchestration
- Dependency management
- Docker image handling

### Stack (da_vinci_cdk.stack)
- Base stack class
- Common stack utilities

## Contribution Guidelines

- Depend on da-vinci core package via workspace reference
- Follow CDK best practices
- Make constructs reusable
- Document construct parameters
- Handle stack dependencies explicitly
