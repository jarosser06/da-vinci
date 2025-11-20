# Da Vinci Documentation

This directory contains the source files for Da Vinci's Sphinx-based documentation.

## Building Documentation Locally

### Prerequisites

- Python 3.11+
- uv package manager
- Dependencies installed (`uv sync`)

### Build Commands

**Quick Build:**
```bash
./scripts/build-docs.sh
```

**Manual Build:**
```bash
cd docs
uv run sphinx-build -M html . _build
```

**View Built Documentation:**
```bash
open docs/_build/html/index.html
```

## Documentation Structure

```
docs/
├── conf.py                 # Sphinx configuration
├── index.rst              # Documentation homepage
├── overview.rst           # Framework overview
├── installation.rst       # Installation guide
├── quickstart.rst         # Quick start tutorial
├── architecture.rst       # Architecture documentation
├── principles.rst         # Core principles
├── applications.rst       # Application guide
├── stacks.rst            # Stack management
├── tables.rst            # DynamoDB tables guide
├── examples/             # Code examples
│   ├── index.rst
│   ├── basic_crud.rst
│   ├── event_driven.rst
│   ├── multi_table.rst
│   ├── api_backend.rst
│   └── batch_processing.rst
├── api/                  # API reference
│   ├── core.rst         # Core package API
│   └── cdk.rst          # CDK package API
├── migration.rst        # Migration guides
├── contributing.rst     # Contributing guidelines
└── changelog.rst        # Changelog

```

## Infrastructure

### Deploy Documentation Hosting

The documentation is hosted on S3 with CloudFront CDN.

#### Option 1: Without Custom Domain

Deploy with CloudFront URL only:

```bash
./infrastructure/deploy-docs-infrastructure.sh da-vinci-docs
```

This creates:
- S3 bucket for documentation
- CloudFront distribution (generates domain like `d1234abcd.cloudfront.net`)

#### Option 2: With Custom Domain

**Prerequisites:**
- Route53 hosted zone (e.g., `davinciproject.dev`)
- ACM certificate in `us-east-1` for your docs domain

**Step 1: Request Certificate (if needed)**

```bash
# Request certificate in us-east-1 (required for CloudFront)
CERT_ARN=$(aws acm request-certificate \
  --domain-name docs.davinciproject.dev \
  --validation-method DNS \
  --region us-east-1 \
  --query 'CertificateArn' \
  --output text)

# Get DNS validation record and add to Route53
aws acm describe-certificate \
  --certificate-arn $CERT_ARN \
  --region us-east-1 \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord'

# Wait for validation (5-10 minutes)
```

**Step 2: Deploy Infrastructure**

```bash
./infrastructure/deploy-docs-infrastructure.sh \
  da-vinci-docs \
  docs.davinciproject.dev \
  Z1234567890ABC \
  arn:aws:acm:us-east-1:123456789012:certificate/...
```

Parameters:
1. Stack name
2. Domain name
3. Hosted Zone ID
4. Certificate ARN

**Step 3: Configure GitHub Secrets**

```bash
# Source generated environment file
source infrastructure/docs-env.sh

# Set secrets for automated deployment
gh secret set DOCS_S3_BUCKET --body "$DOCS_S3_BUCKET"
gh secret set DOCS_CLOUDFRONT_ID --body "$DOCS_CLOUDFRONT_ID"
```

### Infrastructure Components

- **S3 Bucket:** Stores HTML documentation files
- **CloudFront Distribution:** CDN for fast global access
- **Origin Access Control:** Secure access to S3
- **Route53 (Optional):** Custom domain A record
- **ACM Certificate (Optional):** SSL/TLS for custom domain

### Versioning

Documentation is versioned alongside code releases:

- `/v3.0/` - Specific version
- `/latest/` - Latest release
- `/versions.json` - Version metadata

### Manual Deployment

To deploy documentation manually (outside of release process):

```bash
./scripts/deploy-docs.sh 3.0.0 da-vinci-docs-docs E1234567890ABC
```

## CI/CD Integration

### Continuous Integration

Documentation is built on every commit to verify it compiles correctly:

```yaml
# .github/workflows/ci.yml
- name: Build documentation
  run: ./scripts/build-docs.sh
```

Build failures will block PR merges.

### Release Process

Documentation is deployed only during official releases:

1. Tag new version
2. Build packages
3. Publish to PyPI
4. **Deploy documentation** ← Happens here
5. Create GitHub release

## Writing Documentation

### Adding New Pages

1. Create `.rst` file in `docs/`
2. Add to table of contents in `index.rst` or relevant section
3. Build and verify: `./scripts/build-docs.sh`

### Writing Style

- Use reStructuredText (`.rst`) format
- Include code examples with syntax highlighting
- Add cross-references using `:doc:` role
- Document all public APIs with docstrings

### Code Examples

All code examples should:
- Be working, tested code
- Include complete context
- Show both definition and usage
- Explain key concepts

### API Documentation

API docs are auto-generated from docstrings using Sphinx autodoc:

```python
def my_function(arg1: str, arg2: int) -> bool:
    """
    Brief description.

    Keyword Arguments:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value
    """
```

## Troubleshooting

### Build Warnings

Sphinx may show warnings for:
- Missing docstrings
- Broken cross-references
- Invalid reStructuredText syntax

Fix warnings before committing.

### Module Import Errors

If autodoc can't import modules:
1. Verify `sys.path` in `conf.py`
2. Check package is installed
3. Ensure no circular imports

### S3 Deployment Fails

Check:
- AWS credentials configured
- Bucket exists and is accessible
- CloudFormation stack deployed successfully

## Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [Read the Docs Theme](https://sphinx-rtd-theme.readthedocs.io/)
