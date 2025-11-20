Da Vinci
========
A framework for rapidly developing Python-based AWS Cloud Native applications.

Da Vinci uses AWS CDK for application deployment and infrastructure management. It provides patterns for managing multiple stacks under a single application while handling CloudFormation dependencies.

## Documentation

Full documentation is available at [https://docs.davinciproject.dev/](https://docs.davinciproject.dev/)

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
- AWS-native development patterns
- Infrastructure from table definitions
- Built-in configuration management, error handling, and service communication
- Direct access to AWS services and boto3 when needed

### Design Principles
1. **Stay Close to AWS**: Framework wraps AWS services without hiding them
2. **Eliminate Repetition, Not Control**: Handle boilerplate while preserving flexibility
3. **Operational First**: Built-in patterns for configuration, errors, and events
4. **Single Source of Truth**: Table definitions drive infrastructure

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
