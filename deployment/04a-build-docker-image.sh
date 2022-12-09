#!/bin/bash -e
# Setup env vars
AWS_PROFILE=$1

ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text --profile $AWS_PROFILE)

# INSTRUCTIONS - update with target region
AWS_REGION=$(aws configure get region --profile $AWS_PROFILE)

# Replace with your R53 Alias pointing to your ALB
COMPANY_DOMAIN='<enter_your_domain>'        # example mycompanydomain.com
CLOUDFRONT_CNAME='<enter_cloudfront_cname>' # example ui.mycompanydomain.com
ECR_REPO_NAME='<enter_ecr_repo_name>' # example sftp-backend-0a635743

# Build the image from the source directory
pushd ../source/backend

sed -i -e "s/REPLACE_ME_COMPANY_DOMAIN/$COMPANY_DOMAIN/" src/flask_app_jwt_configuration.json
sed -i -e "s/REPLACE_ME_CLOUDFRONT_CNAME/$CLOUDFRONT_CNAME/" src/flask_app_jwt_configuration.json

sudo docker build -t sftp-backend .

popd

sed -i -e "s/REPLACE_ME_COMPANY_DOMAIN/$COMPANY_DOMAIN/" 06a-add-security-headers.sh

# Log in to ECR and push image
aws ecr get-login-password \
  --region $AWS_REGION \
  --profile $AWS_PROFILE | sudo docker login --username AWS \
  --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

sudo docker tag sftp-backend "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest"

sudo docker push "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest"