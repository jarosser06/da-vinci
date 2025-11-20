# Da Vinci Project Overview

## Purpose
Da Vinci is a framework for rapidly developing Python-based AWS Cloud Native applications. It provides a low-bootstrap cost solution for projects requiring best-practices for rapidly developed software, internal IT, and Intelligent Business Automation.

## Tech Stack
- **Languages**: Python (≥3.11 for core, ≥3.12 for CDK)
- **Infrastructure**: AWS CDK, CloudFormation
- **Package Manager**: uv (workspace-based monorepo)
- **AWS Services**: DynamoDB, Lambda, EventBridge, and other managed services
- **Dependencies**: boto3, requests, aws-cdk-lib, constructs

## Repository Structure
- `packages/core/` - da_vinci core runtime library
- `packages/cdk/` - da_vinci-cdk infrastructure library
- `scripts/` - Build and distribution automation
- `infrastructure/` - Infrastructure as code
- `docs/` - Documentation
- `examples/` - Example applications

## Version
Current version: 2.0.0 (Semantic Versioning)
