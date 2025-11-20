#!/bin/bash

###############################################################################
# setup-certificate.sh - Request and validate ACM certificate for CloudFront
#
# This script creates an ACM certificate in us-east-1 (required for CloudFront)
# and guides you through DNS validation using Route 53.
#
# Usage:
#   ./infrastructure/setup-certificate.sh
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - Route 53 hosted zone already created for your domain
#   - parameters.json configured with DomainName and HostedZoneId
###############################################################################

set -e
set -u

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARAMETERS_FILE="$SCRIPT_DIR/parameters.json"
CERTIFICATE_REGION="us-east-1"  # Required for CloudFront

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

main() {
  echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}  ${GREEN}ACM Certificate Setup for CloudFront${NC}                      ${CYAN}║${NC}"
  echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # Check if parameters file exists
  if [ ! -f "$PARAMETERS_FILE" ]; then
    log_error "parameters.json not found at: $PARAMETERS_FILE"
    log_info "Create parameters.json from the example file first"
    exit 1
  fi

  # Read domain name and hosted zone from parameters
  DOMAIN_NAME=$(jq -r '.[] | select(.ParameterKey=="DomainName") | .ParameterValue' "$PARAMETERS_FILE")
  HOSTED_ZONE_ID=$(jq -r '.[] | select(.ParameterKey=="HostedZoneId") | .ParameterValue' "$PARAMETERS_FILE")

  if [ -z "$DOMAIN_NAME" ] || [ "$DOMAIN_NAME" = "null" ] || [ "$DOMAIN_NAME" = "YOUR_DOMAIN_NAME" ]; then
    log_error "DomainName not set in parameters.json"
    exit 1
  fi

  if [ -z "$HOSTED_ZONE_ID" ] || [ "$HOSTED_ZONE_ID" = "null" ] || [ "$HOSTED_ZONE_ID" = "YOUR_HOSTED_ZONE_ID" ]; then
    log_error "HostedZoneId not set in parameters.json"
    exit 1
  fi

  log_info "Domain: $DOMAIN_NAME"
  log_info "Hosted Zone ID: $HOSTED_ZONE_ID"
  log_info "Certificate Region: $CERTIFICATE_REGION (required for CloudFront)"
  echo ""

  # Check if certificate already exists
  log_info "Checking for existing certificate..."
  EXISTING_CERT=$(aws acm list-certificates \
    --region "$CERTIFICATE_REGION" \
    --query "CertificateSummaryList[?DomainName=='$DOMAIN_NAME'].CertificateArn" \
    --output text)

  if [ -n "$EXISTING_CERT" ]; then
    log_warn "Certificate already exists for $DOMAIN_NAME"
    echo "  Certificate ARN: $EXISTING_CERT"
    echo ""

    # Check certificate status
    CERT_STATUS=$(aws acm describe-certificate \
      --certificate-arn "$EXISTING_CERT" \
      --region "$CERTIFICATE_REGION" \
      --query 'Certificate.Status' \
      --output text)

    log_info "Certificate Status: $CERT_STATUS"

    if [ "$CERT_STATUS" = "ISSUED" ]; then
      log_success "Certificate is already issued and ready to use!"
      update_parameters_file "$EXISTING_CERT"
      exit 0
    elif [ "$CERT_STATUS" = "PENDING_VALIDATION" ]; then
      log_warn "Certificate is pending validation"
      CERT_ARN="$EXISTING_CERT"
    else
      log_error "Certificate status: $CERT_STATUS"
      log_info "You may need to request a new certificate"
      exit 1
    fi
  else
    # Request new certificate
    log_info "Requesting new ACM certificate for $DOMAIN_NAME..."
    CERT_ARN=$(aws acm request-certificate \
      --domain-name "$DOMAIN_NAME" \
      --validation-method DNS \
      --region "$CERTIFICATE_REGION" \
      --query 'CertificateArn' \
      --output text)

    log_success "Certificate requested!"
    echo "  Certificate ARN: $CERT_ARN"
    echo ""

    # Wait for DNS validation record to be available
    log_info "Waiting for validation record information..."
    sleep 5
  fi

  # Get DNS validation records
  log_info "Retrieving DNS validation records..."
  VALIDATION_RECORD=$(aws acm describe-certificate \
    --certificate-arn "$CERT_ARN" \
    --region "$CERTIFICATE_REGION" \
    --query 'Certificate.DomainValidationOptions[0].ResourceRecord' \
    --output json)

  RECORD_NAME=$(echo "$VALIDATION_RECORD" | jq -r '.Name')
  RECORD_VALUE=$(echo "$VALIDATION_RECORD" | jq -r '.Value')
  RECORD_TYPE=$(echo "$VALIDATION_RECORD" | jq -r '.Type')

  echo ""
  log_info "DNS Validation Record:"
  echo "  Name:  $RECORD_NAME"
  echo "  Type:  $RECORD_TYPE"
  echo "  Value: $RECORD_VALUE"
  echo ""

  # Check if validation record already exists
  EXISTING_RECORD=$(aws route53 list-resource-record-sets \
    --hosted-zone-id "$HOSTED_ZONE_ID" \
    --query "ResourceRecordSets[?Name=='$RECORD_NAME' && Type=='$RECORD_TYPE'].ResourceRecords[0].Value" \
    --output text 2>/dev/null || echo "")

  if [ -n "$EXISTING_RECORD" ]; then
    log_warn "Validation record already exists in Route 53"
    log_info "Existing value: $EXISTING_RECORD"

    if [ "$EXISTING_RECORD" = "$RECORD_VALUE" ]; then
      log_success "Record value matches - validation should complete soon"
    else
      log_warn "Record value doesn't match - it may need to be updated"
    fi
  else
    # Create DNS validation record in Route 53
    log_info "Creating DNS validation record in Route 53..."

    CHANGE_BATCH=$(cat <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "$RECORD_NAME",
      "Type": "$RECORD_TYPE",
      "TTL": 300,
      "ResourceRecords": [{"Value": "$RECORD_VALUE"}]
    }
  }]
}
EOF
)

    CHANGE_ID=$(aws route53 change-resource-record-sets \
      --hosted-zone-id "$HOSTED_ZONE_ID" \
      --change-batch "$CHANGE_BATCH" \
      --query 'ChangeInfo.Id' \
      --output text)

    log_success "DNS record created!"
    echo "  Change ID: $CHANGE_ID"
    echo ""
  fi

  # Wait for certificate validation
  log_info "Waiting for certificate validation..."
  log_warn "This can take several minutes (usually 5-10 minutes)"
  echo ""

  MAX_ATTEMPTS=60
  ATTEMPT=0

  while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    CERT_STATUS=$(aws acm describe-certificate \
      --certificate-arn "$CERT_ARN" \
      --region "$CERTIFICATE_REGION" \
      --query 'Certificate.Status' \
      --output text)

    if [ "$CERT_STATUS" = "ISSUED" ]; then
      echo ""
      log_success "Certificate validated and issued!"
      break
    elif [ "$CERT_STATUS" = "PENDING_VALIDATION" ]; then
      echo -n "."
      sleep 10
      ATTEMPT=$((ATTEMPT + 1))
    else
      echo ""
      log_error "Certificate status: $CERT_STATUS"
      exit 1
    fi
  done

  if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo ""
    log_warn "Validation timeout - certificate is still pending"
    log_info "Certificate ARN: $CERT_ARN"
    log_info "You can check status with:"
    echo "  aws acm describe-certificate --certificate-arn $CERT_ARN --region $CERTIFICATE_REGION"
    exit 1
  fi

  echo ""
  update_parameters_file "$CERT_ARN"
}

update_parameters_file() {
  local CERT_ARN=$1

  log_info "Updating parameters.json with certificate ARN..."

  # Update CertificateArn in parameters.json
  jq --arg arn "$CERT_ARN" \
    'map(if .ParameterKey == "CertificateArn" then .ParameterValue = $arn else . end)' \
    "$PARAMETERS_FILE" > "${PARAMETERS_FILE}.tmp"

  mv "${PARAMETERS_FILE}.tmp" "$PARAMETERS_FILE"

  log_success "Updated parameters.json"
  echo ""

  echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}  ${GREEN}Certificate Setup Complete!${NC}                             ${CYAN}║${NC}"
  echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo "Certificate ARN: $CERT_ARN"
  echo ""
  echo "Next steps:"
  echo "  1. Deploy infrastructure: ${YELLOW}./infrastructure/deploy.sh${NC}"
  echo "  2. Set up GitHub secrets: ${YELLOW}./infrastructure/setup-github-secrets.sh${NC}"
  echo ""
}

# Run main function
main
