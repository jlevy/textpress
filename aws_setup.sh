aws iam create-user --user-name s3-publish-all
aws iam attach-user-policy --user-name s3-publish-all --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam attach-user-policy --user-name s3-publish-all --policy-arn arn:aws:iam::aws:policy/CloudFrontFullAccess
aws iam create-access-key --user-name s3-publish-all

aws configure --profile s3-publish-all

