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
import json
import boto3
from botocore import config
import os
import datetime
import urllib.request, urllib.parse
import uuid
from datetime import timedelta

boto_config = json.loads(os.environ['botoConfig'])
config = config.Config(**boto_config)


def lambda_handler(event, context):
  responseData = {}
  stack_id = str(os.environ['STACK_ID'])
  ecs_cluster_name = str(os.environ['ECSClusterName'])
  CognitoUserPoolId = str(os.environ['CognitoUserPoolId'])
  url = str(os.environ['url'])
  responseData['solutionId'] = str(os.environ['solutionId'])
  responseData['version'] = str(os.environ['version'])
  responseData['uuid'] = str(uuid.uuid4())
  responseData['timestmp'] = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S:%S"))
  responseData['metrics'] = str(os.environ['metrics'])
  responseData['cognito_users'] = str(get_current_users(CognitoUserPoolId, config))
  ecs_stats = get_ecs_stats(ecs_cluster_name, config)
  responseData['ecs_cluster_status'] = ecs_stats[0]
  responseData['fargate_running_tasks'] = ecs_stats[1]

  responseData['network_tx'] = str(get_network_tx(ecs_cluster_name, config)) + "MB"
  responseData['network_rx'] = str(get_network_rx(ecs_cluster_name, config)) + "MB"

  # Send metrics data
  send_anonymous_metric(responseData, url)


# Get current users
def get_current_users(CognitoUserPoolId, config):
  client = boto3.client('cognito-idp', config=config)
  response = client.describe_user_pool(
    UserPoolId=CognitoUserPoolId
  )
  users = response.get("UserPool").get("EstimatedNumberOfUsers")
  return users


# Get ecs stats
def get_ecs_stats(ecs_cluster_name, config):
  client = boto3.client('ecs', config=config)
  response = client.describe_clusters(
    clusters=[
      ecs_cluster_name,
    ],
    include=['STATISTICS']
  )
  status = response.get('clusters')[0].get('status')
  statistics = response.get('clusters')[0].get('statistics')
  task_count = (next(item for item in statistics if item["name"] == "runningFargateTasksCount")).get('value')
  return status, task_count


# Get network tx stats
def get_network_tx(ecs_cluster_name, config):
  client = boto3.client('cloudwatch', config=config)
  count = 0
  response = client.get_metric_statistics(
    Namespace="ECS/ContainerInsights",
    MetricName="NetworkTxBytes",
    Dimensions=[
      {
        "Name": "ClusterName",
        "Value": ecs_cluster_name
      },
    ],
    StartTime=datetime.datetime.now() - timedelta(days=1),
    EndTime=datetime.datetime.now(),
    Period=300,
    Statistics=[
      "Sum",
    ]
  )
  # print(response)
  for r in response['Datapoints']:
    count = count + (r['Sum'])
  return count / 1024 / 1024

# Get network rx stats
def get_network_rx(ecs_cluster_name, config):
  client = boto3.client('cloudwatch', config=config)
  count = 0
  response = client.get_metric_statistics(
    Namespace="ECS/ContainerInsights",
    MetricName="NetworkRxBytes",
    Dimensions=[
      {
        "Name": "ClusterName",
        "Value": ecs_cluster_name
      },
    ],
    StartTime=datetime.datetime.now() - timedelta(days=1),
    EndTime=datetime.datetime.now(),
    Period=300,
    Statistics=[
      "Sum",
    ]
  )
  # print(response)
  for r in response['Datapoints']:
    count = count + (r['Sum'])
  return count / 1024 / 1024

# Send data
def send_anonymous_metric(payload, url):
  if (payload != None):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(payload).encode())
    req.add_header('Content-Type', 'application/json')
    response = urllib.request.urlopen(req)
    print(response.read())
  else:
    print("empty payload")
