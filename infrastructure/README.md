# Da Vinci PyPI Infrastructure

CloudFormation-based infrastructure for hosting a private PyPI repository on S3.

## Quick Setup

### With Custom Domain (CloudFront)

```bash
# 1. Create parameters file
cp infrastructure/parameters.json.example infrastructure/parameters.json
# Edit parameters.json with your values:
#   - ProjectName: "da-vinci"
#   - DomainName: "packages.davinciproject.dev"
#   - HostedZoneId: (from Route 53)

# 2. Set up SSL certificate (us-east-1 for CloudFront)
./infrastructure/setup-certificate.sh

# 3. Deploy infrastructure
./infrastructure/deploy.sh

# 4. Set up GitHub secrets
./infrastructure/setup-github-secrets.sh
```

### Without Custom Domain (S3-only)

```bash
# 1. Create parameters file
cp infrastructure/parameters.json.example infrastructure/parameters.json
# Edit parameters.json - leave DomainName, HostedZoneId, CertificateArn empty

# 2. Deploy infrastructure
./infrastructure/deploy.sh

# 3. Set up GitHub secrets
./infrastructure/setup-github-secrets.sh
```

## Infrastructure Components

### S3 Bucket
- **Purpose**: Hosts Python packages in PyPI simple format
- **Public Access**: Read-only access to `/simple/*` path
- **Versioning**: Enabled (90-day retention for old versions)
- **Encryption**: AES256 server-side encryption

### IAM Deployment User
- **Purpose**: CI/CD deployments and package uploads
- **Permissions**:
  - S3: Read, write, delete objects in PyPI bucket
  - CloudFormation: Read stack information
- **Access Keys**: Created optionally with `--create-access-key`

## Deployment

### Initial Setup

1. **Create parameters file:**
   ```bash
   cp infrastructure/parameters.json.example infrastructure/parameters.json
   ```

2. **Edit parameters.json** with your values:
   ```json
   [
     {
       "ParameterKey": "ProjectName",
       "ParameterValue": "my-company"
     },
     {
       "ParameterKey": "Environment",
       "ParameterValue": "production"
     }
   ]
   ```

3. **Deploy infrastructure:**
   ```bash
   ./infrastructure/deploy.sh
   ```

**Parameters (in parameters.json):**
- `ProjectName` - Your organization/project name (e.g., "acme-corp")
- `Environment` - Environment tag (production/staging/development)

**Script Options:**
- `--region REGION` - AWS region (default: us-east-1)

**Output:**
- Bucket name derived as: `{ProjectName}-pypi-{Environment}`
- CloudFormation stack deployed
- IAM deployment user created
- Configuration saved to `infrastructure/config.sh`

### GitHub Secrets Setup

After deploying infrastructure, set up GitHub Actions credentials:

```bash
./infrastructure/setup-github-secrets.sh
```

**Features:**
- **Automatic**: Uses GitHub CLI (`gh`) to set secrets directly
- **Idempotent**: Safe to run multiple times
- **Rotation**: Use `--rotate` flag to refresh credentials

**What it does:**
- Creates IAM access key for deployment user
- Sets these GitHub repository secrets:
  - `AWS_PYPI_ACCESS_KEY_ID`
  - `AWS_PYPI_SECRET_ACCESS_KEY`
  - `AWS_PYPI_REGION`
  - `AWS_PYPI_BUCKET`
- Provides manual instructions if `gh` CLI not installed

**Rotating credentials:**
```bash
./infrastructure/setup-github-secrets.sh --rotate
```

### Update Existing Stack

```bash
./infrastructure/deploy.sh
```

CloudFormation will update only changed resources. Parameters are read from `infrastructure/parameters.json`.

## Configuration

After deployment, configuration is saved to `infrastructure/config.sh`:

```bash
export S3_PYPI_BUCKET="my-company-pypi"
export AWS_REGION="us-east-1"
export DEPLOYMENT_USER="my-company-pypi-deployer-production"
```

**Load configuration:**
```bash
source infrastructure/config.sh
```

**Add credentials (not saved to file):**
```bash
export AWS_ACCESS_KEY_ID="<access-key-id>"
export AWS_SECRET_ACCESS_KEY="<secret-access-key>"
```

Or use AWS CLI profile:
```bash
export AWS_PROFILE="pypi-deployer"
```

## Security

### Sensitive Files (Git Ignored)

The following files are automatically ignored by `.gitignore`:
- `infrastructure/config.sh` - May contain credentials
- `*.pem` - Private keys
- `*.key` - Access keys

### Access Key Management

**Never commit access keys to Git!**

For GitHub Actions, store credentials as repository secrets:
- `AWS_PYPI_ACCESS_KEY_ID`
- `AWS_PYPI_SECRET_ACCESS_KEY`
- `AWS_PYPI_REGION`

**Rotate access keys regularly:**
```bash
# Re-run with --create-access-key to rotate
./infrastructure/deploy.sh --bucket-name my-company-pypi --create-access-key
```

This deletes old keys and creates new ones.

## S3 Bucket Structure

```
s3://my-company-pypi/
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

## Usage

### Upload Packages

```bash
source infrastructure/config.sh
./scripts/distribute.sh
```

### Install Packages

```bash
pip install --extra-index-url https://my-company-pypi.s3.us-east-1.amazonaws.com/simple/ da-vinci
```

### requirements.txt

```
--extra-index-url https://my-company-pypi.s3.us-east-1.amazonaws.com/simple/
da-vinci==2.0.0
da-vinci-cdk==2.0.0
```

## CloudFormation Template

`pypi-s3.yaml` includes:

**Resources:**
- `PyPIBucket` - S3 bucket for packages
- `PyPIBucketPolicy` - Public read access to /simple/*
- `DeploymentUser` - IAM user for CI/CD
- `DeploymentPolicy` - IAM policy for deployment user

**Outputs:**
- `BucketName` - S3 bucket name
- `BucketURL` - PyPI index URL
- `DeploymentUserArn` - IAM user ARN
- `DeploymentUserName` - IAM user name
- `InstallationCommand` - Example pip install command

## Troubleshooting

### "Stack already exists"
The deployment script automatically updates existing stacks.

### "Access Denied" when uploading
1. Verify AWS credentials: `aws sts get-caller-identity`
2. Check you're using deployment user credentials
3. Verify IAM policy is attached

### "Package not found" after upload
1. Check S3 bucket contents: `aws s3 ls s3://my-company-pypi/simple/da-vinci/`
2. Verify index.html exists and is valid
3. Check pip cache: `pip cache purge`

### "Invalid credentials"
Rotate access keys:
```bash
./infrastructure/deploy.sh --bucket-name my-company-pypi --create-access-key
```

## Cost Estimation

**S3 Storage:**
- ~$0.023 per GB/month (Standard tier)
- Typical package size: ~50KB per wheel
- 100 versions ≈ 5MB ≈ $0.001/month

**S3 Requests:**
- GET requests: $0.0004 per 1,000 requests
- PUT requests: $0.005 per 1,000 requests

**Data Transfer:**
- First 1 GB/month: Free
- Next 9.999 TB: $0.09 per GB

**Estimated monthly cost for small team (< 100 downloads/day):**
- ~$0.10 - $1.00/month

## Cleanup

To delete the infrastructure:

```bash
# Empty the bucket first (S3 buckets cannot be deleted with contents)
aws s3 rm s3://my-company-pypi --recursive

# Delete the CloudFormation stack
aws cloudformation delete-stack \
  --stack-name my-company-pypi-pypi-infrastructure \
  --region us-east-1

# Delete access keys manually if needed
aws iam delete-access-key \
  --user-name my-company-pypi-deployer-production \
  --access-key-id <access-key-id>
```

## Alternative: CloudFront Distribution

For better performance with many users, add CloudFront:

1. Create CloudFront distribution with S3 origin
2. Update bucket policy to allow CloudFront OAC
3. Use CloudFront URL instead of S3 URL

This is not included in the base template to keep costs low for small teams.

## References

- [PEP 503: Simple Repository API](https://peps.python.org/pep-0503/)
- [AWS S3 Static Website Hosting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- [pip Extra Index URLs](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-extra-index-url)
