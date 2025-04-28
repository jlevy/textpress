#!/bin/bash

set -euo pipefail

export BUCKET="texpr-pub-prod"
export REGION="us-west-2"

# Create the bucket
aws s3api create-bucket \
  --bucket $BUCKET \
  --region $REGION \
  --create-bucket-configuration LocationConstraint=$REGION

# Disable the Block Public Access settings on that bucket
aws s3api put-public-access-block \
  --bucket $BUCKET \
  --public-access-block-configuration \
    BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false

# Attach a “public-read” bucket policy
cat > public-read-policy.json <<EOF
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"AllowPublicRead",
      "Effect":"Allow",
      "Principal":"*",
      "Action":"s3:GetObject",
      "Resource":"arn:aws:s3:::$BUCKET/*"
    }
  ]
}
EOF

aws s3api put-bucket-policy \
  --bucket $BUCKET \
  --policy file://public-read-policy.json

# (Optional) Verify your policy is in place
aws s3api get-bucket-policy --bucket $BUCKET

# Now you can sync/upload and objects will be publicly readable:
# aws s3 sync ./mycontent s3://$BUCKET/targetfolder/ --acl public-read
