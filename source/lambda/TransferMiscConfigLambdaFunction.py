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

import json, os, boto3, uuid
from botocore import config
import cfnresponse

boto_config = json.loads(os.environ['botoConfig'])
config = config.Config(**boto_config)

def lambda_handler(event, context):
    print(event)
    stack_id = str(os.environ['STACK_ID'])
    print("stack_id:" + stack_id)
    # Handle Cloudformation Delete event
    if(event.get('RequestType') == 'Delete'):
        #print(event)
        LogicalResourceId = event.get("LogicalResourceId")

        # Delete CognitoClientSecret SSM Parameter
        ssmclient = boto3.client('ssm', config=config)
        try:
          print("Deleting CognitoClientSecret SSM Parameter")
          response = ssmclient.delete_parameter(
            Name='sftpui-CognitoClientSecret-' + stack_id
          )
          print("Deleted CognitoClientSecret SSM Parameter")
        except ssmclient.exceptions.ParameterNotFound:
          print ("CognitoClientSecret not found in Parameter Store")

        # Delete JWTSecretKey SSM Parameter
        try:
          print("Deleting JWTSecretKey SSM Parameter")
          response = ssmclient.delete_parameter(
            Name='sftpui-JWTSecretKey-' + stack_id
          )
          print("Deleted JWTSecretKey SSM Parameter")
        except ssmclient.exceptions.ParameterNotFound:
          print ("JWTSecretKey not found in Parameter Store")

        responseData = {}
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData, LogicalResourceId)

    # Handle Cloudformation Update event
    if(event.get('RequestType') == 'Update'):
        #print(event)
        LogicalResourceId = event.get("LogicalResourceId")
        responseData = {}
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData, LogicalResourceId)

    if(event.get('RequestType') == 'Create'):
        #print(event)
        LogicalResourceId = event.get("LogicalResourceId")
        TransferServerId = event.get("ResourceProperties").get("TransferServerId")
        TransferServerArn = event.get("ResourceProperties").get("TransferServerArn")
        print("Logical Resource ID from the template: " + str(LogicalResourceId))
        print("SFTP Endpoint ID: " + str(TransferServerId))
        print("SFTP Endpoint Arn:" + str(TransferServerArn))

        #Get VPCE ID for AWS Transfer
        client = boto3.client('transfer', config=config)
        response = client.describe_server(
            ServerId=TransferServerId
        )
        #print(response)
        VPCEndpointID = response.get("Server").get("EndpointDetails").get("VpcEndpointId")
        print("AWS Transfer VPC Endpoint ID: " + str(VPCEndpointID))

        #Get DNS Entries for the VPC Endpoint
        client = boto3.client('ec2', config=config)
        response = client.describe_vpc_endpoints(
            VpcEndpointIds=[
                VPCEndpointID
            ]
        )
        #print(response)
        DnsName = response.get("VpcEndpoints")[0].get("DnsEntries")[0].get("DnsName")
        print("Main DNS Name for the VPCE:" + str(DnsName))

        # Create JWTSecret SSM Parameter
        # If not present, create one and use that in the subsequent requests
        try:
          ssmclient = boto3.client('ssm', config=config)
          response = ssmclient.get_parameter(
            Name='sftpui-JWTSecretKey-' + stack_id,
            WithDecryption=True
          )
          print ("JWTSecret found in Parameter Store")
        except ssmclient.exceptions.ParameterNotFound:
          print ("JWTSecret not found in Parameter Store. Creating it and storing it in Parameter Store")
          JWTSecret = str(uuid.uuid4())
          response = ssmclient.put_parameter(
            Name='sftpui-JWTSecretKey-' + stack_id,
            Value=JWTSecret,
            Description = "JWT Secret Key",
            Type= 'SecureString',
          )
          print ("Writing it to Parameter Store. " + str(response.get("ResponseMetadata").get("HTTPStatusCode")))

        #After putting the parameter, retrieve it to get its ARN
        JWT_Secret_Parameter_ARN = ""
        try:
          ssmclient = boto3.client('ssm', config=config)
          response = ssmclient.get_parameter(
            Name='sftpui-JWTSecretKey-' + stack_id,
            WithDecryption=True
          )
          print ("JWTSecret found in Parameter Store.Get its ARN")
          print(response)
          JWT_Secret_Parameter_ARN = response.get("Parameter").get("ARN")
        except ssmclient.exceptions.ParameterNotFound:
          print ("After creating it, JWTSecret still not found in Parameter Store.Cannot get its ARN")

        responseData = {}
        responseData['Data'] = DnsName
        responseData['JWT_Secret_Key_Parameter_ARN'] = JWT_Secret_Parameter_ARN
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData, LogicalResourceId)
