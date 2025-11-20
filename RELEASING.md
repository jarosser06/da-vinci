# Release Process

This document describes the complete release workflow for da_vinci packages.

## Overview

Da Vinci uses a monorepo structure with two independently distributable packages:
- **da-vinci** (core) - Runtime library
- **da-vinci-cdk** - CDK infrastructure library

Packages are versioned together using [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH) and distributed via private S3 PyPI.

## Quick Release

```bash
# 1. Bump version
./scripts/bump-version.sh minor  # or major/patch

# 2. Update CHANGELOG.md with changes

# 3. Build, validate, and distribute
./scripts/build.sh && \
./scripts/validate.sh && \
./scripts/distribute.sh --bucket your-pypi-bucket

# 4. Commit and push
git add -A
git commit -m "Release version 2.1.0"
git push && git push --tags
```

## Detailed Release Steps

### 1. Prepare for Release

**Check current state:**
```bash
git status                    # Ensure clean working directory
./test.sh --coverage          # Run tests (90%+ coverage required)
./lint.sh                     # Run linting (zero errors required)
```

**Merge feature work:**
- Ensure all feature branches are merged to `main`
- All CI checks passing
- All PR reviews approved

### 2. Version Bump

Use the automated version bumping script:

```bash
# Bump major version (breaking changes)
./scripts/bump-version.sh major

# Bump minor version (new features, backward compatible)
./scripts/bump-version.sh minor

# Bump patch version (bug fixes, backward compatible)
./scripts/bump-version.sh patch

# Or specify explicit version
./scripts/bump-version.sh 2.1.5
```

**What this does:**
- Updates version following SemVer (MAJOR.MINOR.PATCH)
- Updates `packages/core/pyproject.toml` version
- Updates `packages/cdk/pyproject.toml` version
- Pins CDK dependency to exact core version (`da-vinci==MAJOR.MINOR.PATCH`)
- Adds new version header to `CHANGELOG.md`
- Regenerates `uv.lock`
- Creates git tag `vMAJOR.MINOR.PATCH`

**Manual steps after bump:**
1. Fill in `CHANGELOG.md` with actual changes:
   - Added features
   - Changed functionality
   - Fixed bugs
2. Review the changes: `git diff`

### 3. Build Packages

```bash
./scripts/build.sh
```

**What this does:**
- Builds wheel files for both packages
- Validates Dockerfile is included in core package
- Checks version consistency
- Outputs to `packages/*/dist/*.whl`

**Options:**
```bash
./scripts/build.sh --clean    # Clean previous builds first
./scripts/build.sh --core     # Build core only
./scripts/build.sh --cdk      # Build CDK only
```

### 4. Validate Release

```bash
./scripts/validate.sh
```

**What this validates:**
- Git working directory is clean
- Versions consistent across packages
- All linting checks pass
- All tests pass with 90%+ coverage
- Built wheels exist and are valid
- Dockerfile included in core package
- Packages import correctly

**Options:**
```bash
./scripts/validate.sh --quick        # Skip slow tests
./scripts/validate.sh --allow-dirty  # Allow uncommitted changes
```

### 5. Distribute to S3 PyPI

```bash
./scripts/distribute.sh --bucket your-pypi-bucket
```

**What this does:**
- Validates S3 bucket access
- Uploads wheels to S3 simple index structure
- Generates/updates `index.html` for package discovery
- Sets correct content-type headers
- Provides installation instructions

**Options:**
```bash
./scripts/distribute.sh --bucket my-bucket --dry-run  # Preview only
./scripts/distribute.sh --bucket my-bucket --core     # Core only
./scripts/distribute.sh --bucket my-bucket --cdk      # CDK only
```

**Environment variables:**
```bash
export S3_PYPI_BUCKET=my-company-pypi  # Default bucket
export AWS_PROFILE=my-profile          # AWS CLI profile
export AWS_REGION=us-east-1            # AWS region
```

### 6. Commit and Push

```bash
git add -A
git commit -m "Release version 2.1.0"
git push && git push --tags
```

## Versioning Scheme

**Format:** MAJOR.MINOR.PATCH ([Semantic Versioning](https://semver.org/))

- `MAJOR` - Incompatible API changes
- `MINOR` - Backward-compatible functionality additions
- `PATCH` - Backward-compatible bug fixes

**Examples:**
- `2.0.0` - Major version 2, initial release
- `2.1.0` - Added new features, backward compatible
- `2.0.1` - Bug fixes only, backward compatible
- `3.0.0` - Breaking changes (incompatible with 2.x)

**How it works:**
- Use `./scripts/bump-version.sh major/minor/patch` to increment automatically
- Or specify exact version: `./scripts/bump-version.sh 2.1.5`
- CDK package always pins to exact core version for stability
- Version numbers are never reused

## S3 PyPI Setup

### Initial Setup

1. **Create S3 bucket:**
   ```bash
   aws s3 mb s3://your-pypi-bucket --region us-east-1
   ```

2. **Configure bucket policy** (for public read):
   ```bash
   aws s3api put-bucket-policy --bucket your-pypi-bucket --policy '{
     "Version": "2012-10-17",
     "Statement": [{
       "Sid": "PublicReadGetObject",
       "Effect": "Allow",
       "Principal": "*",
       "Action": "s3:GetObject",
       "Resource": "arn:aws:s3:::your-pypi-bucket/simple/*"
     }]
   }'
   ```

3. **Set environment variable:**
   ```bash
   echo 'export S3_PYPI_BUCKET=your-pypi-bucket' >> ~/.bashrc
   ```

### S3 Structure

```
s3://your-pypi-bucket/
└── simple/
    ├── da-vinci/
    │   ├── index.html
    │   ├── da_vinci-2.0.0-py3-none-any.whl
    │   └── da_vinci-2.1.0-py3-none-any.whl
    └── da-vinci-cdk/
        ├── index.html
        ├── da_vinci_cdk-2.0.0-py3-none-any.whl
        └── da_vinci_cdk-2.1.0-py3-none-any.whl
```

### IAM Permissions for CI/CD

For automated uploads, create IAM user/role with:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-pypi-bucket",
        "arn:aws:s3:::your-pypi-bucket/*"
      ]
    }
  ]
}
```

## Installation

### From S3 PyPI

**Single install:**
```bash
pip install --extra-index-url https://your-bucket.s3.us-east-1.amazonaws.com/simple/ da-vinci
```

**requirements.txt:**
```
--extra-index-url https://your-bucket.s3.us-east-1.amazonaws.com/simple/
da-vinci==2.1.0
da-vinci-cdk==2.1.0
```

**pip.conf (permanent):**
```ini
[global]
extra-index-url = https://your-bucket.s3.us-east-1.amazonaws.com/simple/
```

## Troubleshooting

### Build Issues

**Dockerfile not found:**
- Dockerfile must be in `packages/core/da_vinci/Dockerfile`
- Configured in `packages/core/pyproject.toml`:
  ```toml
  [tool.hatch.build.targets.wheel.force-include]
  "da_vinci/Dockerfile" = "da_vinci/Dockerfile"
  ```
- Rebuild: `./scripts/build.sh --clean`

**Version mismatch:**
- Always use `./scripts/bump-version.sh` to update versions
- Never manually edit version numbers
- CDK must pin exact core version: `da-vinci==YYYY.MM.PP`

### Test/Lint Failures

**Coverage below 90%:**
```bash
./test.sh --coverage  # See coverage report
# Add tests to reach 90%
```

**Linting errors:**
```bash
./lint.sh            # See errors
./lint.sh --fix      # Auto-fix formatting issues
# Manually fix remaining errors
```

### Distribution Issues

**S3 access denied:**
```bash
aws s3 ls s3://your-bucket  # Test access
aws configure                # Check credentials
# Verify bucket policy and IAM permissions
```

**Package not found after upload:**
- Check index.html exists: `aws s3 ls s3://your-bucket/simple/da-vinci/`
- Verify URL format: `https://bucket.s3.region.amazonaws.com/simple/`
- Clear pip cache: `pip cache purge`

## Release Checklist

- [ ] All tests passing (90%+ coverage)
- [ ] All linting checks passing (zero errors)
- [ ] Feature branches merged to main
- [ ] Version bumped with `./scripts/bump-version.sh`
- [ ] CHANGELOG.md updated with changes
- [ ] Packages built with `./scripts/build.sh`
- [ ] Validation passed with `./scripts/validate.sh`
- [ ] Distributed to S3 with `./scripts/distribute.sh`
- [ ] Changes committed and pushed
- [ ] Git tag pushed
- [ ] Installation tested from S3 PyPI
- [ ] Team notified of new release

## Rollback

If a release has issues:

1. **Install previous version:**
   ```bash
   pip install --extra-index-url https://bucket.s3.region.amazonaws.com/simple/ da-vinci==2.0.0
   ```

2. **Delete bad release from S3:**
   ```bash
   aws s3 rm s3://your-bucket/simple/da-vinci/da_vinci-2.1.0-py3-none-any.whl
   aws s3 rm s3://your-bucket/simple/da-vinci-cdk/da_vinci_cdk-2.1.0-py3-none-any.whl
   # Regenerate index.html
   ./scripts/distribute.sh --bucket your-bucket  # Re-uploads index with remaining versions
   ```

3. **Revert git tag:**
   ```bash
   git tag -d v2.1.0
   git push origin :refs/tags/v2.1.0
   ```

4. **Fix issues and re-release with new patch version**

## Best Practices

1. **Always test locally before releasing:**
   ```bash
   python -m venv test_env
   source test_env/bin/activate
   pip install packages/core/dist/*.whl
   python -c "import da_vinci; print('Success')"
   ```

2. **Keep CHANGELOG.md up to date** - Write changes as you go, not at release time

3. **Use semantic commits** - Makes CHANGELOG generation easier

4. **Test S3 installation** after each release

5. **Monitor S3 costs** for high-download scenarios

6. **Keep old versions in S3** for rollback capability (configure lifecycle rules if needed)

7. **Coordinate releases** - Core and CDK released together, always

8. **Document breaking changes** clearly in CHANGELOG.md

## Emergency Hotfix Process

For critical production bugs:

1. Create hotfix branch from main: `git checkout -b hotfix/critical-bug`
2. Fix the bug and test thoroughly
3. Bump patch version: `./scripts/bump-version.sh patch`
4. Build, validate, distribute: `./scripts/build.sh && ./scripts/validate.sh && ./scripts/distribute.sh`
5. Commit, push, and merge immediately
6. Tag and notify team

For hotfixes, the normal PR review process can be expedited but should not be skipped.
