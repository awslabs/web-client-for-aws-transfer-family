# Deprecation Notice
This AWS Solution has been archived and is no longer maintained by AWS. To discover other solutions, please visit the [AWS Solutions Library](https://aws.amazon.com/solutions/).

# Web Client for AWS Transfer Family

AWS customers are looking for ways to provide simple browser-based user interfaces to their corporate SFTP environments. Many of their non-technical users find it inconvenient to use thick client tools such as FileZilla and others. Moreover, many customers do not want to install and support different clients on various end user devices and operating systems. By adopting an intuitive and browser-based solution they reduce the effort of managing commercial or open-source client and having to troubleshoot different end-user devices and operating systems. 
The solution supports common file operations such as Upload, Download, Rename and Delete.

You can find step-by-step implementation guide to deploy this solution here: https://aws.amazon.com/solutions/implementations/web-client-for-aws-transfer-family/?did=sl_card&trk=sl_card



### Uploading and Downloading large files
The Gunicorn connection timeout is set to 600 seconds for sync workers. In order to upload and download files of large sizes, you can adjust the timeout value to be set at higher interval. This could be done by modifying the Dockerfile (from your local clone of the project under `dist/source/backend/Dockerfile` path), line#43:

````
ENTRYPOINT gunicorn --bind 0.0.0.0:80 transfer_sftp_backend:app --timeout 600
````

You may also want to adjust the idle timeout value on the ALB using steps outlined here: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/application-load-balancers.html#connection-idle-timeout


***

Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License Version 2.0 (the "License"). You may not use this file except in compliance with the 
License. A copy of the License is located at

    http://www.apache.org/licenses/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR 
CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and 
limitations under the License.
