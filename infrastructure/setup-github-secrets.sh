#!/bin/bash

###############################################################################
# setup-github-secrets.sh - Create IAM access keys and configure GitHub secrets
#
# This script creates access keys for the GitHub Actions deployment user
# and automatically configures GitHub repository secrets using the GitHub CLI.
#
# Usage:
#   ./infrastructure/setup-github-secrets.sh           # Initial setup (idempotent)
#   ./infrastructure/setup-github-secrets.sh --rotate  # Rotate existing credentials
#
# Environment Variables (optional):
#   AWS_PROFILE    AWS CLI profile to use
#   AWS_REGION     AWS region (default: us-east-1)
#
# Features:
#   - Idempotent: Safe to run multiple times, only creates secrets if missing
#   - Auto-rotation: Use --rotate flag to delete old keys and create new ones
#   - GitHub CLI integration: Automatically sets repository secrets if gh is installed
#   - Reads configuration from infrastructure/parameters.json
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARAMETERS_FILE="$SCRIPT_DIR/parameters.json"
AWS_REGION="${AWS_REGION:-us-west-2}"
ROTATE_MODE=false

# Parse command line arguments
if [[ "${1:-}" == "--rotate" ]]; then
  ROTATE_MODE=true
fi

# AWS CLI profile flag
AWS_PROFILE_FLAG=""
if [[ -n "${AWS_PROFILE:-}" ]]; then
  AWS_PROFILE_FLAG="--profile ${AWS_PROFILE}"
fi

###############################################################################
# Helper Functions
###############################################################################

log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

###############################################################################
# Main Script
###############################################################################

main() {
  if [[ "$ROTATE_MODE" == true ]]; then
    log_info "Rotating GitHub Secrets for da_vinci PyPI deployment"
  else
    log_info "Setting up GitHub Secrets for da_vinci PyPI deployment"
  fi
  echo ""

  # Check if parameters file exists
  if [ ! -f "$PARAMETERS_FILE" ]; then
    log_error "parameters.json not found at: $PARAMETERS_FILE"
    log_info "Create parameters.json from the example file first"
    exit 1
  fi

  # Read parameters from file
  PROJECT_NAME=$(jq -r '.[] | select(.ParameterKey=="ProjectName") | .ParameterValue' "$PARAMETERS_FILE")
  ENVIRONMENT=$(jq -r '.[] | select(.ParameterKey=="Environment") | .ParameterValue' "$PARAMETERS_FILE")

  if [ -z "$PROJECT_NAME" ] || [ "$PROJECT_NAME" = "null" ]; then
    log_error "ProjectName not found in parameters.json"
    exit 1
  fi

  if [ -z "$ENVIRONMENT" ] || [ "$ENVIRONMENT" = "null" ]; then
    ENVIRONMENT="production"
  fi

  # Derive stack name and user name
  STACK_NAME="${PROJECT_NAME}-pypi-infrastructure"
  DEPLOYMENT_USER="${PROJECT_NAME}-pypi-deployer-${ENVIRONMENT}"

  log_info "Project: $PROJECT_NAME | Environment: $ENVIRONMENT | Region: $AWS_REGION"
  echo ""

  # Check AWS credentials
  if ! aws sts get-caller-identity --region "$AWS_REGION" $AWS_PROFILE_FLAG &> /dev/null; then
    log_error "AWS credentials not configured or invalid"
    exit 1
  fi

  # Get the deployment user ARN from CloudFormation
  log_info "Fetching deployment user from CloudFormation stack..."
  USER_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='DeploymentUserArn'].OutputValue" \
    --output text \
    $AWS_PROFILE_FLAG)

  if [[ -z "$USER_ARN" ]]; then
    log_error "Could not retrieve deployment user ARN from stack outputs"
    log_error "Make sure the infrastructure stack '$STACK_NAME' exists and is complete"
    log_info "Run: ./infrastructure/deploy.sh"
    exit 1
  fi

  # Extract username from ARN
  USERNAME=$(echo "$USER_ARN" | awk -F'/' '{print $NF}')
  log_info "Deployment user: $USERNAME"
  echo ""

  # Check if GitHub secrets already exist (idempotent check)
  log_info "Checking if GitHub secrets already exist..."
  SECRETS_EXIST=false

  if command -v gh &> /dev/null; then
    if gh secret list 2>/dev/null | grep -q "AWS_PYPI_ACCESS_KEY_ID"; then
      SECRETS_EXIST=true
      log_info "GitHub secrets already configured"
    fi
  fi

  # Check if access keys already exist
  EXISTING_KEYS=$(aws iam list-access-keys \
    --user-name "$USERNAME" \
    --query 'AccessKeyMetadata[*].AccessKeyId' \
    --output text \
    $AWS_PROFILE_FLAG)

  # If in rotate mode, force deletion and recreation
  if [[ "$ROTATE_MODE" == true ]]; then
    if [[ -n "$EXISTING_KEYS" ]]; then
      log_warn "Rotating credentials - deleting existing access keys..."
      for KEY_ID in $EXISTING_KEYS; do
        log_info "Deleting access key: $KEY_ID"
        aws iam delete-access-key \
          --user-name "$USERNAME" \
          --access-key-id "$KEY_ID" \
          $AWS_PROFILE_FLAG
      done
      log_success "Old access keys deleted"
      echo ""
    else
      log_warn "No existing access keys to rotate"
    fi
    # Clear the existing keys variable so we create new ones
    EXISTING_KEYS=""
  # If secrets exist and access keys exist, we're done (idempotent)
  elif [[ "$SECRETS_EXIST" == true && -n "$EXISTING_KEYS" ]]; then
    log_success "GitHub secrets and AWS access keys already configured"
    log_info "Setup is complete and idempotent - no changes needed"
    echo ""
    echo -e "${GREEN}Existing access key IDs:${NC} $EXISTING_KEYS"
    echo ""
    log_info "To rotate credentials, run: $0 --rotate"
    exit 0
  fi

  # Create new access key if needed
  ACCESS_KEY_ID=""
  SECRET_ACCESS_KEY=""

  if [[ -n "$EXISTING_KEYS" ]]; then
    log_warn "Access keys already exist but GitHub secrets are not configured"
    echo -e "${YELLOW}Existing access key IDs:${NC}"
    echo "$EXISTING_KEYS"
    echo ""
    log_error "Cannot retrieve secret access key for existing keys"
    log_info "You must delete the existing key and create a new one, or manually add secrets"
    echo ""
    read -p "Do you want to delete the old key and create a new one? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      log_info "Exiting without creating new access key"
      exit 0
    fi
    echo ""

    # Delete all existing keys
    for KEY_ID in $EXISTING_KEYS; do
      log_info "Deleting access key: $KEY_ID"
      aws iam delete-access-key \
        --user-name "$USERNAME" \
        --access-key-id "$KEY_ID" \
        $AWS_PROFILE_FLAG
    done
    log_success "Old access keys deleted"
    echo ""
  fi

  # Create new access key
  log_info "Creating new access key for user: $USERNAME"
  ACCESS_KEY_JSON=$(aws iam create-access-key \
    --user-name "$USERNAME" \
    $AWS_PROFILE_FLAG)

  ACCESS_KEY_ID=$(echo "$ACCESS_KEY_JSON" | jq -r '.AccessKey.AccessKeyId')
  SECRET_ACCESS_KEY=$(echo "$ACCESS_KEY_JSON" | jq -r '.AccessKey.SecretAccessKey')

  if [[ -z "$ACCESS_KEY_ID" || -z "$SECRET_ACCESS_KEY" ]]; then
    log_error "Failed to create access key"
    exit 1
  fi

  log_success "Access key created successfully!"
  echo ""

  # Get bucket name and docs infrastructure from stack outputs
  BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" \
    --output text \
    $AWS_PROFILE_FLAG)

  DOCS_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='DocsBucketName'].OutputValue" \
    --output text \
    $AWS_PROFILE_FLAG 2>/dev/null || echo "")

  DOCS_DIST_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='DocsDistributionId'].OutputValue" \
    --output text \
    $AWS_PROFILE_FLAG 2>/dev/null || echo "")

  # Check if GitHub CLI is available for automatic secret management
  if command -v gh &> /dev/null; then
    log_info "GitHub CLI detected - automatically adding secrets to repository..."
    echo ""

    # Set GitHub secrets using gh CLI
    if gh secret set AWS_PYPI_ACCESS_KEY_ID -b"$ACCESS_KEY_ID" && \
       gh secret set AWS_PYPI_SECRET_ACCESS_KEY -b"$SECRET_ACCESS_KEY" && \
       gh secret set AWS_PYPI_REGION -b"$AWS_REGION" && \
       gh secret set AWS_PYPI_BUCKET -b"$BUCKET_NAME"; then

      log_success "GitHub secrets configured successfully!"
      echo ""
      echo -e "${GREEN}Configured secrets:${NC}"
      echo "  - AWS_PYPI_ACCESS_KEY_ID: $ACCESS_KEY_ID"
      echo "  - AWS_PYPI_SECRET_ACCESS_KEY: ****** (hidden)"
      echo "  - AWS_PYPI_REGION: $AWS_REGION"
      echo "  - AWS_PYPI_BUCKET: $BUCKET_NAME"

      # Set docs secrets if infrastructure exists
      if [[ -n "$DOCS_BUCKET" && "$DOCS_BUCKET" != "None" ]]; then
        log_info "Configuring documentation secrets..."
        if gh secret set DOCS_S3_BUCKET -b"$DOCS_BUCKET" && \
           gh secret set DOCS_CLOUDFRONT_ID -b"$DOCS_DIST_ID"; then
          echo "  - DOCS_S3_BUCKET: $DOCS_BUCKET"
          echo "  - DOCS_CLOUDFRONT_ID: $DOCS_DIST_ID"
          log_success "Documentation secrets configured!"
        else
          log_warn "Failed to set documentation secrets"
        fi
      else
        log_info "Documentation infrastructure not deployed - skipping docs secrets"
      fi
      echo ""

      log_success "Setup complete! CI/CD pipeline is ready for automated deployments."
    else
      log_error "Failed to set GitHub secrets automatically"
      log_info "Falling back to manual instructions..."
      echo ""
      display_manual_instructions
    fi
  else
    log_warn "GitHub CLI (gh) not found - displaying manual instructions"
    log_info "Install gh CLI for automatic secret management: https://cli.github.com/"
    echo ""
    display_manual_instructions
  fi
}

display_manual_instructions() {
  # Display instructions for GitHub Secrets
  echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║                     GITHUB REPOSITORY SECRETS                              ║${NC}"
  echo -e "${CYAN}╠════════════════════════════════════════════════════════════════════════════╣${NC}"
  echo -e "${CYAN}║${NC} Add the following secrets to your GitHub repository:                      ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC} Settings → Secrets and variables → Actions → New repository secret        ${CYAN}║${NC}"
  echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
  echo ""

  echo -e "${GREEN}Secret Name:${NC} AWS_PYPI_ACCESS_KEY_ID"
  echo -e "${YELLOW}Value:${NC}"
  echo "$ACCESS_KEY_ID"
  echo ""

  echo -e "${GREEN}Secret Name:${NC} AWS_PYPI_SECRET_ACCESS_KEY"
  echo -e "${YELLOW}Value:${NC}"
  echo "$SECRET_ACCESS_KEY"
  echo ""

  echo -e "${GREEN}Secret Name:${NC} AWS_PYPI_REGION"
  echo -e "${YELLOW}Value:${NC}"
  echo "$AWS_REGION"
  echo ""

  echo -e "${GREEN}Secret Name:${NC} AWS_PYPI_BUCKET"
  echo -e "${YELLOW}Value:${NC}"
  echo "$BUCKET_NAME"
  echo ""

  # Add docs secrets if they exist
  if [[ -n "$DOCS_BUCKET" && "$DOCS_BUCKET" != "None" ]]; then
    echo -e "${GREEN}Secret Name:${NC} DOCS_S3_BUCKET"
    echo -e "${YELLOW}Value:${NC}"
    echo "$DOCS_BUCKET"
    echo ""

    echo -e "${GREEN}Secret Name:${NC} DOCS_CLOUDFRONT_ID"
    echo -e "${YELLOW}Value:${NC}"
    echo "$DOCS_DIST_ID"
    echo ""
  fi

  echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║                          IMPORTANT NOTES                                   ║${NC}"
  echo -e "${CYAN}╠════════════════════════════════════════════════════════════════════════════╣${NC}"
  echo -e "${CYAN}║${NC} • This is the ONLY time you will see the secret access key               ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC} • Store these credentials securely if needed                              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC} • Each IAM user can have a maximum of 2 access keys                       ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC} • To rotate credentials, run: ./infrastructure/setup-github-secrets.sh --rotate ${CYAN}║${NC}"
  echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # Save to temporary file (optional)
  TEMP_FILE=$(mktemp)
  cat > "$TEMP_FILE" <<EOF
GitHub Repository Secrets for da_vinci PyPI
============================================

Add these secrets to your GitHub repository settings:
Settings → Secrets and variables → Actions → New repository secret

AWS_PYPI_ACCESS_KEY_ID
$ACCESS_KEY_ID

AWS_PYPI_SECRET_ACCESS_KEY
$SECRET_ACCESS_KEY

AWS_PYPI_REGION
$AWS_REGION

AWS_PYPI_BUCKET
$BUCKET_NAME

EOF

  # Add docs secrets to temp file if they exist
  if [[ -n "$DOCS_BUCKET" && "$DOCS_BUCKET" != "None" ]]; then
    cat >> "$TEMP_FILE" <<EOF
DOCS_S3_BUCKET
$DOCS_BUCKET

DOCS_CLOUDFRONT_ID
$DOCS_DIST_ID

EOF
  fi

  cat >> "$TEMP_FILE" <<EOF
Created: $(date)
User: $USERNAME
Project: $PROJECT_NAME
Environment: $ENVIRONMENT
EOF

  log_info "Credentials also saved to temporary file: $TEMP_FILE"
  log_warn "Remember to delete this file after adding secrets to GitHub!"
  echo ""
  log_success "Setup complete! Add the secrets to GitHub to enable automated deployments."
}

# Run main function
main
