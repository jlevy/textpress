#!/usr/bin/env bash
set -euo pipefail

# Check required inputs
missing_vars=()
[[ -z "${BUCKET-}" ]] && missing_vars+=("BUCKET (environment variable)")
[[ -z "${ROOT_DOMAIN-}" ]] && missing_vars+=("ROOT_DOMAIN (environment variable)")
[[ -z "${AWS_PROFILE-}" ]] && missing_vars+=("AWS_PROFILE (environment variable)")
[[ -z "${AWS_REGION-}" ]] && missing_vars+=("AWS_REGION (environment variable)")

if [[ ${#missing_vars[@]} -gt 0 ]]; then
  echo "Error: Missing required environment variables:" >&2
  printf " - %s\n" "${missing_vars[@]}" >&2
  echo "Usage: S3_BUCKET=... ROOT_DOMAIN=... AWS_PROFILE=... AWS_REGION=... ./create-cf-s3-only.sh" >&2
  exit 1
fi

# Print configuration and ask for confirmation
echo "Configuration:"
echo "  S3 Bucket:    $BUCKET"
echo "  Root Domain:  $ROOT_DOMAIN"
echo "  AWS Profile:  $AWS_PROFILE"
echo "  AWS Region:   $AWS_REGION (for ACM cert)"
echo

read -p "Proceed with creating CloudFront distribution? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy](es)?$ ]]; then
  echo "Aborted."
  exit 0
fi

echo "Proceeding..."
echo
set -x


# 1) Find or request ACM wildcard cert for *.$ROOT_DOMAIN
CERT_ARN=$(aws acm list-certificates \
  --region "$AWS_REGION" \
  --profile "$AWS_PROFILE" \
  --query "CertificateSummaryList[?DomainName=='$ROOT_DOMAIN'].[CertificateArn]" \
  --output text)

if [ -z "$CERT_ARN" ]; then
  echo "No ACM *.${ROOT_DOMAIN} found. Requesting one (DNS validation)…"
  CERT_ARN=$(aws acm request-certificate \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --domain-name "$ROOT_DOMAIN" \
    --subject-alternative-names "*.$ROOT_DOMAIN" \
    --validation-method DNS \
    --query CertificateArn --output text)
  echo "Requested cert ARN: $CERT_ARN"
  echo "Please add the DNS record shown by:"
  echo "  aws acm describe-certificate --certificate-arn $CERT_ARN --region $AWS_REGION --profile $AWS_PROFILE --query 'Certificate.DomainValidationOptions'"
  exit 0
fi

echo "Using certificate ARN: $CERT_ARN"

# 2) Write the minimal distribution config
CONF="cf-s3-only-config.json"
cat > "$CONF" <<EOF
{
  "CallerReference": "$(date +%s)",
  "Aliases": {
    "Quantity": 1,
    "Items": ["$ROOT_DOMAIN"]
  },
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3Origin",
        "DomainName": "${BUCKET}.s3.amazonaws.com",
        "S3OriginConfig": { "OriginAccessIdentity": "" }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3Origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET","HEAD"]
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": { "Forward": "none" }
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  },
  "ViewerCertificate": {
    "ACMCertificateArn": "$CERT_ARN",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2019"
  },
  "Enabled": true
}
EOF

echo "Creating CloudFront distribution (S3 only)…"
OUT=$(aws cloudfront create-distribution \
  --profile "$AWS_PROFILE" \
  --distribution-config file://"$CONF" \
  --output json)

# parse with jq if available
if command -v jq >/dev/null 2>&1; then
  ID=$(jq -r .Distribution.Id <<<"$OUT")
  DOMAIN=$(jq -r .Distribution.DomainName <<<"$OUT")
else
  ID=$(echo "$OUT" | grep -o '"Id":[^,]*' | head -1 | cut -d\" -f4)
  DOMAIN=$(echo "$OUT" | grep -o '"DomainName":[^,]*' | head -1 | cut -d\" -f4)
fi

echo
echo "✅ Distribution created!"
echo "  ID:   $ID"
echo "  URL:  $DOMAIN"
echo
echo "Point your DNS ($ROOT_DOMAIN) to CloudFront:"
echo "  • Route53: ALIAS $ROOT_DOMAIN → $DOMAIN"
echo "  • Registrar: CNAME $ROOT_DOMAIN → $DOMAIN"

echo
echo "Now upload your site under /pub/:"
echo "  aws s3 sync ./mycontent s3://$BUCKET/pub/ --acl public-read"
echo
echo "Requests to https://$ROOT_DOMAIN/pub/index.html will serve from S3."
echo "All other paths will 404 until you add a server origin."