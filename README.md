# Web Client for AWS Transfer Family
AWS customers are looking for ways to provide simple browser-based user interfaces to their corporate SFTP environments. Many of their non-technical users find it inconvenient to use thick client tools such as FileZilla and others. Moreover, many customers do not want to install and support different clients on various end user devices and operating systems. By adopting an intuitive and browser-based solution they reduce the effort of managing commercial or open-source client and having to troubleshoot different end-user devices and operating systems. 
The solution supports common file operations such as Upload, Download, Rename and Delete.

You can find an AWS infrastructure diagram and list of resources that will be provisioned here: https://aws.amazon.com/solutions/implementations/web-client-for-aws-transfer-family/?did=sl_card&trk=sl_card


### Uploading and Downloading large files
The Gunicorn connection timeout is set to 600 seconds for sync workers. In order to upload and download files of large sizes, you can adjust the timeout value to be set at higher interval. This could be done by modifying the Dockerfile (from your local clone of the project under `dist/source/backend/Dockerfile` path), line#43:

````
ENTRYPOINT gunicorn --bind 0.0.0.0:80 transfer_sftp_backend:app --timeout 600
````

You may also want to adjust the idle timeout value on the ALB using steps outlined here: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/application-load-balancers.html#connection-idle-timeout


### Step-By-Step Deployment Instructions
1. Clone this reposititory  `git clone https://github.com/AkiraMD/web-client-for-aws-transfer-family.git`
2. `cd deployment`
3. Allow user execute: `chmod u+x build-dist.sh` and `chmod u+x build-s3-dist.sh`
4. Run `build-dist.sh`. For example, for nonp `./build-dist.sh thvc-nonp-sftp-web-client-lambda-code thvc-nonp-sftp-web-client v1.0.0`
5. Run `build-s3-dist.sh`. For example, for nonp `./build-s3-dist.sh thvc-nonp-sftp-web-client-lambda-code thvc-nonp-sftp-web-client v1.0.0`
6. Create a `.gitignore` in `dist/.gitignore` with the following entries. Please note that this path will only exist after running the scripts above

```
source/frontend/node_modules/*
source/frontend/dist/sftp-ng-webui/*
```

7. Create an S3 bucket, and key prefix. For example, S3Bucket: "thvc-nonp-sftp-web-client-lambda-code", KeyPrefix: "thvc-nonp-sftp-web-client/v1.0.0", i.e. folders, AND the AWS Lambda code zip files must be uploaded into the S3 bucket and folders. For example, thvc-nonp-sftp-web-client-lambda-code/thvc-nonp-sftp-web-client/v1.0.0/<file_name>.zip. The ZIP files will be located in `deployment/regional-s3-assets/lambda`. Please note that this path will only exist after running the scripts above
8. Create an S3 bucket for the AWS Transfer Family server to use. For example, in nonp "thvc-nonp-sftp"
9.  Create each stack in AWS Cloudformation from the templates in `dist/deployment`. Please note that this path will only exist after running the scripts above
10. Please note that the script `06a-add-security-headers.sh` calls the Cloudformation template `06b-security-headers-lambda-edge.template` and creates resources that have to be in AWS region us-east-1. DO NOT create a stack for `06b-security-headers-lambda-edge.template` manually
11. Create users in the AWS Cognito User Pool console. You need to ensure each user is: Email verified: Yes, Confirmation status: Confirmed, and Status: Enabled. Please see `07b-cognito-seed.sh` for examples on how to do this
12. Create an ACM certificate, for example, Domain: sftpui.stg.virtualcare.telushealth.com, in us-east-1, AND that you have clicked the "Create records in Route 53" button and that the certificate is Status: Issued
13. The Cloudformation templates will create the ACM certificate, for example, Domain: sftpapi.stg.virtualcare.telushealth.com, needed for the load balancer, BUT again you have clicked the "Create records in Route 53" button and ensure that the certificate is Status: Issued
14. Create a DynamoDB item, in the table created in `03-sftp-endpoint.template` for each Cognito user that maps their username to the AWS Transfer Family server bucket and user folder created. Here is an example JSON DynamoDB item that needs to be created for each user:

```
{
  "username": {
    "S": "thvcnonpsftptest"
  },
  "directoryMap": {
    "S": "[{\"Entry\": \"/thvcnonpsftptest\", \"Target\": \"/thvc-nonp-sftp/thvcnonpsftptest\"}]"
  }
}
```

15. Now you should be able to login where you configured your UI domain. For example, `https://sftpui.stg.virtualcare.telushealth.com`

***

Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License Version 2.0 (the "License"). You may not use this file except in compliance with the 
License. A copy of the License is located at

    http://www.apache.org/licenses/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR 
CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and 
limitations under the License.
