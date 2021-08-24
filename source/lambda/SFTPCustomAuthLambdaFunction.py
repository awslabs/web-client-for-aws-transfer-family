#########################################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.                    #
# SPDX-License-Identifier: MIT-0                                                        #
#                                                                                       #
# Permission is hereby granted, free of charge, to any person obtaining a copy of this  #
# software and associated documentation files (the "Software"), to deal in the Software #
# without restriction, including without limitation the rights to use, copy, modify,    #
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to    #
# permit persons to whom the Software is furnished to do so.                            #
#                                                                                       #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,   #
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A         #
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT    #
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION     #
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE        #
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                #
#########################################################################################

import boto3
import json,logging,botocore.exceptions,hmac,hashlib,base64,os
from botocore import config

boto_config = json.loads(os.environ['botoConfig'])
config = config.Config(**boto_config)

dynamodb = boto3.resource('dynamodb', config=config)
table = dynamodb.Table(os.environ['SFTPUSRDIRMAP'])


def lambda_handler(event, context):
  stack_id = str(os.environ['STACK_ID'])
  role_arn = str(os.environ['ROLE_ARN'])
  #print("stack_id:" + stack_id)
  response = {}
  if "username" not in event or "serverId" not in event or "password" not in event:
    return response

  server_id = event["serverId"]
  uname = event["username"]
  pas = event["password"]
  #bucketname = "${AWSTransferForSFTPS3Bucket}"

  if (pas != ""):
    status_code = auth_with_cognito(uname, pas, stack_id)
    if status_code[0] != None:
        auth_result = status_code[0]["AuthenticationResult"]
        response["Role"] = role_arn
        response['HomeDirectoryType'] = "LOGICAL"
        response['HomeDirectoryDetails'] = get_user_directory_mapping(uname)
        return response
    else:
        print("Failed to authenticate user {} with Cognito.".format(uname))
  else:
    print("Failed to authenticate user as the password is blank")

# This function authenticates a user with Cognito and returns a status code
def auth_with_cognito(uname, pas, stack_id):
  USER_POOL_ID = os.environ['USER_POOL_ID']
  CLIENT_ID = os.environ['CLIENT_ID']
  CLIENT_SECRET = ""
  client = boto3.client('cognito-idp', config=config)
  #Cognito Client Secret from Para Store
  try:
    ssmclient = boto3.client('ssm', config=config)
    response = ssmclient.get_parameter(
      Name='sftpui-CognitoClientSecret-' + stack_id,
      WithDecryption=True
    )
    CLIENT_SECRET = response.get("Parameter").get("Value")
  except ssmclient.exceptions.ParameterNotFound:
    response = client.describe_user_pool_client(
      UserPoolId= USER_POOL_ID,
      ClientId=CLIENT_ID
    )
    CLIENT_SECRET = response.get("UserPoolClient").get("ClientSecret")
    if(CLIENT_SECRET != None or CLIENT_SECRET != ""):
      response = ssmclient.put_parameter(
        Name='sftpui-CognitoClientSecret-' + stack_id,
        Value=CLIENT_SECRET,
        Description = "Cognito User Pool Client Secret",
        Type= 'SecureString',
      )
  secret_hash = get_secret_hash(uname, CLIENT_ID, CLIENT_SECRET)
  try:
    resp = client.admin_initiate_auth(UserPoolId=USER_POOL_ID, ClientId=CLIENT_ID, AuthFlow='ADMIN_NO_SRP_AUTH',
               AuthParameters={ 'USERNAME': uname, 'SECRET_HASH': secret_hash, 'PASSWORD': pas },
              ClientMetadata={ 'username': uname, 'password': pas})
  except client.exceptions.NotAuthorizedException:
      return None, "The uname or pass is incorrect"
  except client.exceptions.UserNotConfirmedException:
      return None, "User is not confirmed"
  except Exception as e:
      return None, e.__str__()
  return resp, None

def get_secret_hash(user_name, CLIENT_ID, CLIENT_SECRET):
  msg = user_name + CLIENT_ID
  dig = hmac.new(str(CLIENT_SECRET).encode('utf-8'),
  msg = str(msg).encode('utf-8'), digestmod=hashlib.sha256).digest()
  d2 = base64.b64encode(dig).decode()
  return d2

#Get user mapping
def get_user_directory_mapping(uname):
  try:
    response = table.get_item(Key={'username': uname})
    directoryMap = response['Item'].get("directoryMap")
    directoryMap = json.dumps(directoryMap)
    return directoryMap
  except Exception as e:
    return None, e.__str__()