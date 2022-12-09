#!/bin/bash -e
# Setup env vars
AWS_PROFILE=$1

# Replace with your preferred domain name
DOMAIN_NAME='REPLACE_ME_COMPANY_DOMAIN' # NOTE: example, 'mycompanydomain.com'

# Create Cloudformation stack that creates Lambda@Edge function in US-East-1
stack_name="sftp-sec-hdr-stack-$(echo $RANDOM)"
echo $stack_name

# This template needs to be deployed in US-EAST-1 as Lambda@Edge functions are currently
# required to be in US-EAST-1 region
aws cloudformation create-stack --stack-name $stack_name --template-body file://06b-security-headers-lambda-edge.template --parameters ParameterKey=DomainName,ParameterValue=$DOMAIN_NAME \
 --profile $AWS_PROFILE --region us-east-1 --capabilities CAPABILITY_IAM

# Print the value of Lambda@Edge version, which will be need in Cloudfront distribution configuration next.
lambda_edge_version=$(aws cloudformation describe-stacks --stack-name $stack_name --profile $AWS_PROFILE --region us-east-1 | grep OutputValue)
while [ -z "$lambda_edge_version" ] ; do # check for null
  lambda_edge_version=$(aws cloudformation describe-stacks --stack-name $stack_name --profile $AWS_PROFILE --region us-east-1 | grep OutputValue)
  echo "Waiting for stack to complete its creation."
  sleep 10
done
echo $lambda_edge_version
