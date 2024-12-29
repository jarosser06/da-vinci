### Overview
The Stack class is the foundation for all infrastructure stacks in Da Vinci CDK. It extends AWS CDK's Stack
class, adding framework-specific functionality and standardization.

### Core Functionality
- Standardized stack naming (`app_name-deployment_id-stack_name`)
- Stack dependency management
- Docker image configuration
- Framework feature requirements (Event Bus, Exception Trap)

### Stack Dependencies
Stacks can declare dependencies on other stacks, which the framework automatically resolves during deployment:

```python
class CustomStack(Stack):
    def __init__(self, ...):
        super().__init__(
            required_stacks=[DatabaseStack, StorageStack],
            ...
        )
```

### Framework Integration
In addition to the normal dependency declaration, framework stacks can be toggled as dependencies using
feature flags. It is always a best practice to specify dependence on the Da Vinci feature stacks when being utilized.

- `requires_event_bus`: Stack utilizes event loop functionality, either publishing or recieving
- `requires_exceptions_trap`: Stack manages code that is expecting exceptions to be trapped