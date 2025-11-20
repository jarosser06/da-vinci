# Da Vinci Build & Distribution Scripts

Automation scripts for building, versioning, and distributing the da_vinci monorepo packages.

> **For complete release workflow, see [RELEASING.md](../RELEASING.md)**

## Scripts

### bump-version.sh

Synchronizes version across both packages and updates dependencies.

**Usage:**
```bash
./scripts/bump-version.sh <version>
./scripts/bump-version.sh 2025.4.21
```

**What it does:**
- Validates version format (YYYY.MM.PP)
- Updates `packages/core/pyproject.toml` version
- Updates `packages/cdk/pyproject.toml` version
- Sets CDK dependency to exact core version (`da-vinci==YYYY.MM.PP`)
- Updates `CHANGELOG.md` with new version header
- Creates git tag `vYYYY.MM.PP`
- Regenerates `uv.lock`

**Example:**
```bash
$ ./scripts/bump-version.sh 2025.4.21
Bumping version to 2025.4.21

Current versions:
  Core: 2025.4.20
  CDK:  2025.4.20

New version: 2025.4.21

Continue? (y/n) y
→ Updating packages/core/pyproject.toml...
→ Updating packages/cdk/pyproject.toml...
→ Updating CHANGELOG.md...
→ Updating uv.lock...
→ Creating git tag v2025.4.21...
✓ Version bump complete!
```

### build.sh

Builds wheel files for both packages with validation.

**Usage:**
```bash
./scripts/build.sh              # Build all packages
./scripts/build.sh --core       # Build core package only
./scripts/build.sh --cdk        # Build CDK package only
./scripts/build.sh --clean      # Clean before building
```

**What it does:**
- Cleans previous builds (optional)
- Builds wheel files using hatchling
- Validates Dockerfile is included in core package
- Checks version consistency
- Generates build report

**Example:**
```bash
$ ./scripts/build.sh
╔════════════════════════════════════════╗
║   Da Vinci Package Build System       ║
╚════════════════════════════════════════╝

Building core package...
→ Building wheel...
✓ Built: da_vinci-2025.4.20-py3-none-any.whl
→ Validating Dockerfile inclusion...
✓ Dockerfile is included in package

Building CDK package...
→ Building wheel...
✓ Built: da_vinci_cdk-2025.4.20-py3-none-any.whl

Validating builds...
→ Core package: da-vinci 2025.4.20
  Size: 42K
→ CDK package: da-vinci-cdk 2025.4.20
  Size: 38K
→ Checking version consistency...
✓ Versions match: 2025.4.20

╔════════════════════════════════════════╗
║   Build Complete!                      ║
╚════════════════════════════════════════╝
```

**Output:**
- `packages/core/dist/*.whl` - Core package wheel
- `packages/cdk/dist/*.whl` - CDK package wheel

### validate.sh

Pre-distribution validation to ensure quality standards.

**Usage:**
```bash
./scripts/validate.sh              # Run all validations
./scripts/validate.sh --quick      # Skip slow tests
./scripts/validate.sh --allow-dirty # Allow uncommitted changes
```

**What it validates:**
- Git working directory is clean (no uncommitted changes)
- Version consistency between packages
- All linting checks pass (flake8, black, isort, mypy)
- All tests pass with 90%+ coverage
- Built wheels exist and are valid
- Dockerfile included in core package
- Package imports work correctly

**Example:**
```bash
$ ./scripts/validate.sh
╔════════════════════════════════════════╗
║   Da Vinci Pre-Distribution Validation║
╚════════════════════════════════════════╝

→ Checking git status...
✓ Working directory clean

→ Checking version consistency...
✓ Versions consistent: 2025.4.20

→ Running linting checks...
✓ All linting checks passed

→ Running tests with coverage...
✓ All tests passed (92% coverage)

→ Checking built packages...
✓ Built packages found
  Core: da_vinci-2025.4.20-py3-none-any.whl
  CDK:  da_vinci_cdk-2025.4.20-py3-none-any.whl
✓ Dockerfile included in core package

→ Validating package imports...
✓ Core package imports successfully

════════════════════════════════════════
✓ All validations passed!

Ready to distribute:
  ./scripts/distribute.sh --bucket <your-bucket>
```

### distribute.sh

Publishes packages to S3 PyPI with proper index generation.

**Usage:**
```bash
./scripts/distribute.sh --bucket <bucket-name>              # Distribute all
./scripts/distribute.sh --bucket <bucket-name> --core       # Core only
./scripts/distribute.sh --bucket <bucket-name> --cdk        # CDK only
./scripts/distribute.sh --bucket <bucket-name> --dry-run    # Preview
```

**Environment Variables:**
- `S3_PYPI_BUCKET` - Default S3 bucket name
- `AWS_PROFILE` - AWS CLI profile to use
- `AWS_REGION` - AWS region (default: us-east-1)

**What it does:**
- Validates S3 bucket access
- Uploads wheel files to S3 simple index structure
- Generates/updates `index.html` for package discovery
- Sets correct content-type headers
- Provides installation instructions

**S3 Structure:**
```
s3://your-pypi-bucket/
└── simple/
    ├── da-vinci/
    │   ├── index.html
    │   ├── da_vinci-2025.4.20-py3-none-any.whl
    │   └── da_vinci-2025.4.21-py3-none-any.whl
    └── da-vinci-cdk/
        ├── index.html
        ├── da_vinci_cdk-2025.4.20-py3-none-any.whl
        └── da_vinci_cdk-2025.4.21-py3-none-any.whl
```

**Example:**
```bash
$ export S3_PYPI_BUCKET=my-company-pypi
$ ./scripts/distribute.sh --bucket my-company-pypi
╔════════════════════════════════════════╗
║   Da Vinci S3 PyPI Distribution       ║
╚════════════════════════════════════════╝

Target: all
Bucket: s3://my-company-pypi
Region: us-east-1

→ Verifying S3 bucket access...
✓ Bucket accessible

Uploading da-vinci...
  Local:  packages/core/dist/da_vinci-2025.4.20-py3-none-any.whl
  Remote: s3://my-company-pypi/simple/da-vinci/da_vinci-2025.4.20-py3-none-any.whl
✓ Uploaded da_vinci-2025.4.20-py3-none-any.whl
→ Generating index.html for da-vinci...
✓ Updated index.html

Uploading da-vinci-cdk...
  Local:  packages/cdk/dist/da_vinci_cdk-2025.4.20-py3-none-any.whl
  Remote: s3://my-company-pypi/simple/da-vinci-cdk/da_vinci_cdk-2025.4.20-py3-none-any.whl
✓ Uploaded da_vinci_cdk-2025.4.20-py3-none-any.whl
→ Generating index.html for da-vinci-cdk...
✓ Updated index.html

╔════════════════════════════════════════╗
║   Distribution Complete!               ║
╚════════════════════════════════════════╝

Installation Instructions:

  # Configure pip to use private index
  pip install --extra-index-url https://my-company-pypi.s3.us-east-1.amazonaws.com/simple/ da-vinci

  # Or add to requirements.txt:
  --extra-index-url https://my-company-pypi.s3.us-east-1.amazonaws.com/simple/
  da-vinci
  da-vinci-cdk

PyPI Index URLs:
  Core: https://my-company-pypi.s3.us-east-1.amazonaws.com/simple/da-vinci/
  CDK:  https://my-company-pypi.s3.us-east-1.amazonaws.com/simple/da-vinci-cdk/
```

---

For complete release workflow, AWS setup, installation instructions, and troubleshooting, see [RELEASING.md](../RELEASING.md).
