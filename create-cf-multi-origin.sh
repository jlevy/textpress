#!/usr/bin/env bash
set -euo pipefail

# create-cf-multi-origin.sh
# Usage: ./create-cf-multi-origin.sh <S3_BUCKET> <ROOT_DOMAIN> <SERVER_ORIGIN_DOMAIN>
# Example: ./create-cf-multi-origin.sh texpr-pub-prod texpr.com api.texpr.com

if [ $# -ne 3 ]; then
  echo "Usage: $0 <S3_BUCKET> <ROOT_DOMAIN> <SERVER_ORIGIN_DOMAIN>"
  exit 1
fi

BUCKET="$1"
ROOT_DOMAIN="$2"
SERVER_ORIGIN="$3"
PROFILE="${AWS_PROFILE:-default}"
REGION="us-east-1"   # ACM certs for CloudFront must be in us-east-1

echo "→ Using bucket:      $BUCKET"
echo "→ Root domain:       $ROOT_DOMAIN"
echo "→ Server origin:     $SERVER_ORIGIN"
echo "→ AWS profile:       $PROFILE"
echo "→ ACM region:        $REGION"
echo

# 1) Find or request ACM wildcard certificate for *.texpr.com
CERT_ARN=$(aws acm list-certificates \
  --region "$REGION" \
  --profile "$PROFILE" \
  --query "CertificateSummaryList[?DomainName=='*.$ROOT_DOMAIN'].[CertificateArn]" \
  --output text)

if [ -z "$CERT_ARN" ]; then
  echo "→ No existing wildcard cert for *.$ROOT_DOMAIN found. Requesting new one..."
  CERT_ARN=$(aws acm request-certificate \
    --region "$REGION" \
    --profile "$PROFILE" \
    --domain-name "$ROOT_DOMAIN" \
    --subject-alternative-names "*.$ROOT_DOMAIN" \
    --validation-method DNS \
    --output text \
    --query CertificateArn)

  echo
  echo "⚠️  Certificate requested. You must validate via DNS before proceeding."
  echo "Run:"
  echo "  aws acm describe-certificate \\"
  echo "    --certificate-arn $CERT_ARN \\"
  echo "    --region $REGION \\"
  echo "    --profile $PROFILE \\"
  echo "    --query 'Certificate.DomainValidationOptions'"
  exit 0
fi

echo "→ Using ACM certificate ARN: $CERT_ARN"
echo

# 2) Build the distribution config JSON
DIST_CONF="cf-multi-origin-config.json"
cat > "$DIST_CONF" <<EOF
{
  "CallerReference": "$(date +%s)",
  "Aliases": {
    "Quantity": 1,
    "Items": ["$ROOT_DOMAIN"]
  },
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 2,
    "Items": [
      {
        "Id": "S3-static",
        "DomainName": "${BUCKET}.s3.amazonaws.com",
        "OriginPath": "",
        "S3OriginConfig": { "OriginAccessIdentity": "" }
      },
      {
        "Id": "Custom-server",
        "DomainName": "$SERVER_ORIGIN",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "https-only",
          "OriginSslProtocols": {
            "Quantity": 1,
            "Items": ["TLSv1.2_2019"]
          }
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "Custom-server",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": { "Quantity": 2, "Items": ["GET","HEAD"] },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": { "Forward": "none" }
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  },
  "CacheBehaviors": {
    "Quantity": 1,
    "Items": [
      {
        "PathPattern": "pub/*",
        "TargetOriginId": "S3-static",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": { "Quantity": 2, "Items": ["GET","HEAD"] },
        "ForwardedValues": {
          "QueryString": false,
          "Cookies": { "Forward": "none" }
        },
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000
      }
    ]
  },
  "ViewerCertificate": {
    "ACMCertificateArn": "$CERT_ARN",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2019"
  },
  "Enabled": true
}
EOF

echo "→ Distribution config written to $DIST_CONF"
echo

# 3) Create the CloudFront distribution
echo "→ Creating CloudFront distribution..."
CREATE_OUT=$(aws cloudfront create-distribution \
  --profile "$PROFILE" \
  --distribution-config file://"$DIST_CONF" \
  --output json)

# Extract ID and DomainName (requires jq)
if command -v jq >/dev/null 2>&1; then
  DIST_ID=$(jq -r .Distribution.Id <<<"$CREATE_OUT")
  CF_DOMAIN=$(jq -r .Distribution.DomainName <<<"$CREATE_OUT")
else
  DIST_ID=$(echo "$CREATE_OUT" | aws --profile "$PROFILE" \
    cloudfront create-distribution --query 'Distribution.Id' --output text)
  CF_DOMAIN=$(echo "$CREATE_OUT" | aws --profile "$PROFILE" \
    cloudfront create-distribution --query 'Distribution.DomainName' --output text)
fi

echo
echo "✅  Distribution created!"
echo "   ID:   $DIST_ID"
echo "   CNAME: $CF_DOMAIN"
echo
echo "→ Now point your DNS ($ROOT_DOMAIN) to the CloudFront domain:"
echo "    • In Route 53: create an ALIAS record for $ROOT_DOMAIN → $CF_DOMAIN"
echo "    • Or at your DNS provider: CNAME $ROOT_DOMAIN → $CF_DOMAIN"
echo
echo "Requests to https://$ROOT_DOMAIN/pub/* will serve from S3,"
echo "and all other paths will go to https://$SERVER_ORIGIN."