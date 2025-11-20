Overview
========

What is Da Vinci?
-----------------

Da Vinci is a framework for rapidly developing Python-based AWS Cloud Native applications. It provides a set of tools and patterns for building production-ready serverless applications on AWS.

The framework is built around four core principles:

1. **Additive Convenience** - Never blocks direct AWS access
2. **Single Source of Truth** - Centralized configuration and definitions
3. **AWS-Native Development** - Stays close to AWS services
4. **Operational First** - Built-in production-ready patterns

Key Features
------------

**Framework Integration**
   Da Vinci integrates with AWS services while maintaining the flexibility to use boto3 or direct AWS SDK calls when needed.

**DynamoDB Simplified**
   Centralized table definitions that drive both your application code and infrastructure deployment.

**Service Discovery**
   Built-in service discovery mechanisms to connect services across your application.

**Event-Driven Architecture**
   First-class support for event-driven patterns with SQS, EventBridge, and more.

**Infrastructure as Code**
   CDK constructs that generate infrastructure from your application definitions.

**Production Ready**
   Built-in error handling, logging, and operational patterns.

Architecture
------------

Da Vinci consists of two Python packages:

**da_vinci (Core Runtime)**
   The core package provides runtime functionality for your application business logic:

   - DynamoDB table definitions and clients
   - Event handling and publishing
   - Service discovery
   - AWS service integrations
   - Utilities for common operations

**da_vinci_cdk (Infrastructure)**
   The CDK package provides infrastructure constructs:

   - Automatic infrastructure generation from table definitions
   - Stack and application constructs
   - CDK patterns optimized for Da Vinci applications
   - Deployment utilities

These packages work together to provide a complete development experience where your business logic definitions drive both your runtime code and infrastructure deployment.

When to Use Da Vinci
---------------------

Da Vinci is ideal for:

- Building serverless applications on AWS
- Teams that want infrastructure-as-code integrated with application code
- Projects requiring rapid development without sacrificing control
- Applications using DynamoDB as primary datastore
- Event-driven architectures
- Microservices and distributed systems

Da Vinci may not be the best fit if:

- You're not using AWS as your primary cloud provider
- You prefer to keep infrastructure and application code completely separate
- You need to support multiple cloud providers
- Your application doesn't use serverless architectures

Version History
---------------

**Current Version: 3.0.0** (See CHANGELOG for version history)

Da Vinci follows semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR** - Incompatible API changes
- **MINOR** - Backward-compatible functionality additions
- **PATCH** - Backward-compatible bug fixes

Projects should pin to a specific MAJOR.MINOR version for stability. See the :doc:`migration` guide for upgrading between major versions.

License
-------

Da Vinci is released under the MIT License. See the LICENSE file in the repository for full details.

Getting Help
------------

- **Documentation**: You're reading it!
- **GitHub Issues**: `Report bugs or request features <https://github.com/jarosser06/da-vinci/issues>`_
- **Contributing**: See :doc:`contributing` for guidelines
