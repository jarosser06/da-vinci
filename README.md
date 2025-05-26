Da Vinci
========
A framework for rapidly developing Python-based AWS Cloud Native applications.

Da Vinci is ideal for projects that require a low-bootstrap cost but require
best-practices for rapidly developed software, internal IT and Intelligent
Business Automation as examples.

For the application deployment and infrastructure management, Da Vinci is purely
CDK under the hood. It utilitzes a few techniques to manage stacks under a single
umbrella without some of the typical pitfalls that come with CloudFormation dependencies.

The best place to start is reviewing the existing framework stacks located in the CDK library or the 
[example applications](#example-applications) section below.

The framework is split into two libraries:

- `da_vinci` - This is the core library that will be utilized to develop the applcation business logic.
- `da_vinci-cdk` - This is the CDK library that would be utilized to declare the application and AWS resource management.

**WARNING**: CDK `destroy` operations may attempt to delete resources in an incorrect order that violates the defined
dependencies. While deployment honors dependencies correctly, destroy operations can fail due to CDK not properly
reversing the dependency order. Manual cleanup may be required in some cases. 

### Key Features
- **AWS-Native Development**: Leverage AWS services directly while eliminating boilerplate
- **Full-Stack Integration**: Seamless handling of infrastructure (CDK), data, and application layers
- **Production Ready**: Built-in configuration management, error handling, and service communication
- **Flexible Architecture**: Use framework features as needed while maintaining access to raw AWS constructs
- **Battle-Tested**: Powers complex production applications

### Design Principles
1. **Stay Close to AWS**: Framework wraps but doesn't hide AWS services, allowing direct access when needed
2. **Eliminate Repetition, Not Control**: Handle boilerplate while preserving flexibility for complex requirements
3. **Operational First**: Built-in solutions for common production needs (configuration, errors, events)
4. **Single Source of Truth**: Table definitions drive infrastructure, explicit dependencies, centralized configuration

### Versioning
This library uses date-based versioning to indicate API contracts. The version number format is YYYY.MM.PP where:

- `YYYY.MM` indicates the API contract version
- `PP` is a patch number for non-breaking changes and bug fixes

For example: `2024.12.01` and `2024.12.02` maintain the same API contract, while `2025.01.01` indicates potential breaking changes from `2024.12`.

Projects should pin to a specific `YYYY.MM` to maintain stability.

Check the [Changelog](CHANGELOG.md) for specifics about what changed.

### Example Da Vinci CDK Application

```python
from da_vinci_cdk.application import Application

env = 'prototype'

app = Application(
    app_name='my_app',
    deployment_id=f'{env}',
)

app.add_uninitialized_stack(MyAppStack)

app.synth()
```

### Example Applications

[Caylent's Omnilake](https://github.com/caylent/omnilake) is the best current example application/framework that was built using the Da Vinci framework. It makes use of almost every major feature of the framework, including several examples of usage with the ORM.