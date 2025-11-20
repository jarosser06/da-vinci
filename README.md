Da Vinci
========
A framework for rapidly developing Python-based AWS Cloud Native applications.

Da Vinci is ideal for projects that require a low-bootstrap cost but require best-practices for rapidly developed software, internal IT and Intelligent Business Automation as examples.

For application deployment and infrastructure management, Da Vinci is purely CDK under the hood. It utilizes a few techniques to manage stacks under a single umbrella without some of the typical pitfalls that come with CloudFormation dependencies.

## Installation

**Using pip:**
```bash
pip install --extra-index-url https://packages.davinciproject.dev/simple/ da-vinci da-vinci-cdk
```

**Using Poetry:**
```bash
poetry source add --priority=explicit davinciproject https://packages.davinciproject.dev/simple/
poetry add da-vinci --source davinciproject
poetry add da-vinci-cdk --source davinciproject
```

**Using uv:**
```bash
uv add da-vinci da-vinci-cdk --extra-index-url https://packages.davinciproject.dev/simple/
```

## Overview

The framework is split into two libraries:

- **`da_vinci`** - Core runtime library for application business logic
- **`da_vinci-cdk`** - CDK library for infrastructure declarations

**Note**: CDK `destroy` operations may attempt to delete resources in an incorrect order that violates defined dependencies. While deployment honors dependencies correctly, destroy operations can fail due to CDK not properly reversing the dependency order. Manual cleanup may be required in some cases. 

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
This library uses [Semantic Versioning](https://semver.org/) (SemVer). The version number format is MAJOR.MINOR.PATCH where:

- `MAJOR` - Incompatible API changes
- `MINOR` - Backward-compatible functionality additions
- `PATCH` - Backward-compatible bug fixes

For example: `2.0.0`, `2.1.0`, `2.0.1`

Check the [Changelog](CHANGELOG.md) for specifics about what changed.

### Example Da Vinci CDK Application

```python
from da_vinci_cdk.application

env = 'prototype'

app = Application(
    app_name='my_app',
    install_id=f'rosser-{env}',
)

app.synth()
```

### Example Applications

[Ratio](https://github.com/jarosser06/ratio) is the best current example application/framework that
was built using the Da Vinci framework.
