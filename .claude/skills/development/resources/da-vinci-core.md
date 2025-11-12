# Da Vinci Core Package

Contributing to the da_vinci core package.

## Package Structure

### Core Module (da_vinci.core)
- ORM for DynamoDB access
- Settings management
- Logging utilities
- Resource discovery
- Client base classes
- Immutable objects
- Table definitions

### Event Bus Module (da_vinci.event_bus)
- Event publishing and subscription
- Event routing
- Event response handling
- Table definitions for event storage

### Exception Trap Module (da_vinci.exception_trap)
- Exception capture
- Error reporting
- Table definitions for error storage

## Contribution Guidelines

- Check existing patterns in the module you're modifying
- Update table definitions if adding new tables
- Keep Lambda runtime code lightweight
