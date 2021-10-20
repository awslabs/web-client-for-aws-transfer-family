# Setup env vars
AWS_PROFILE=$1

ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text --profile $AWS_PROFILE)

# INSTRUCTIONS - update with target region
AWS_REGION=$(aws configure get region --profile $AWS_PROFILE)

COGNITO_CLIENT_ID=''            # Get from sftp-cognito-stack outputs UserPoolClientId
COGNITO_APP_CLIENT_SECRET=''    # Get from Cognito console for the above client id. 
COGNITO_USER_USERNAME=''        # example mysftpuser
COGNITO_USER_PASSWD=''          # Use upper and lower case characters along with a number and special character, e.g. TempPa$4Me!
COGNITO_USER_TELNUM=''          # example +15555551212
COGNITO_USER_EMAIL_DOMAIN=''    # example acmecorp.com
COGNITO_USERPOOL_ID=''          # Get from sftp-cognito-stack outputs UserPoolId

# Create a user
resp=$(aws cognito-idp admin-create-user \
--user-pool-id $COGNITO_USERPOOL_ID \
--username $COGNITO_USER_USERNAME \
--temporary-password $COGNITO_USER_PASSWD \
--desired-delivery-mediums EMAIL \
--message-action SUPPRESS \
--user-attributes Name=email,Value="$COGNITO_USER_USERNAME@$COGNITO_USER_EMAIL_DOMAIN" Name=phone_number,Value="$COGNITO_USER_TELNUM" \
--profile $AWS_PROFILE)

#Mark Email attributed verified
resp=$(aws cognito-idp admin-update-user-attributes \
--user-pool-id $COGNITO_USERPOOL_ID \
--username $COGNITO_USER_USERNAME \
--user-attributes Name=email_verified,Value=true \
--profile $AWS_PROFILE)

#Reset the password
# Seems like a bug with this command: https://github.com/aws/aws-cli/issues/5675
aws cognito-idp admin-set-user-password \
--user-pool-id $COGNITO_USERPOOL_ID \
--username $COGNITO_USER_USERNAME \
--password $COGNITO_USER_PASSWD \
--permanent \
--profile $AWS_PROFILE