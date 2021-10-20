import datetime
from datetime import timedelta
from datetime import timezone
import os
import logging
import requests
from flask import Flask
from flask import jsonify, send_file, Response, after_this_request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, jwt_required,get_jwt_identity, create_access_token, set_access_cookies, unset_jwt_cookies, get_raw_jwt
)
from auth_util import authenticate_request
from kms_util import encrypt_username_password_boto
from sftp_util import get_sftp_connection, create_sftp_connection
from naming_util import replace_forward_slash, contains_special_characters

import psutil

from flask import make_response, request, current_app
from functools import update_wrapper
import uuid
import boto3
import logging.config
import json

logging.config.fileConfig('logging.conf')
# create logger
logger = logging.getLogger('sftpwebclientlogger')

def crossdomain(origin=None, methods=None, headers=None, max_age=21600,
                attach_to_all=True, automatic_options=True):
    """Decorator function that allows crossdomain requests.
      Courtesy of
      https://blog.skyred.fi/articles/better-crossdomain-snippet-for-flask.html
    """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    # use str instead of basestring if using Python 3.x
    if headers is not None and not isinstance(headers, list):
        headers = ', '.join(x.upper() for x in headers)
    # use str instead of basestring if using Python 3.x
    # if not isinstance(origin, String):
    #     origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        """ Determines which methods are allowed
        """
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        """The decorator function
        """
        def wrapped_function(*args, **kwargs):
            """Caries out the actual cross domain code
            """
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Allow-Headers'] = \
                "Origin, X-Requested-With, Content-Type, Accept, Authorization, x-csrf-token"
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

#Setting SFTP endpoint from the environment variable
env = os.getenv('sftp_hostname')
if not env:
    raise ValueError("SFTP Endpoint not found in env")
else:
    logger.debug(f'sftp_hostname found in the environment variable')

#Setting KMS Key ID from the environment variable
kms_key_id = os.getenv('kms_key_id')
if not kms_key_id:
    raise ValueError("KMS Key ID not found in env")
else:
    logger.debug(f'kms_key_id found in the environment variable')

#Setting JWT Secret Key Parameter Value from the environment variable
jwt_secret_key = os.getenv('jwt_secret_key_parameter_value')
if not jwt_secret_key:
    raise ValueError("jwt_secret_key_parameter_value not found in env")
else:
    logger.info(f'jwt_secret_key found in the environment variable:' + jwt_secret_key)

'''
jwt_secret_key = ""
# Getting JWT Secret Key from parameter store
try:
    ssmclient = boto3.client('ssm')
    response = ssmclient.get_parameter(
        Name=jwt_secret_key_parameter_name,
        WithDecryption=True
    )
    logger.debug(f'JWTSecret found in Parameter Store')
    jwt_secret_key = response.get("Parameter").get("Value")
    logger.info(f'jwt_secret_key value:' + jwt_secret_key)
except ssmclient.exceptions.ParameterNotFound:
    logger.debug(f'JWTSecret not found in Parameter Store.')
    raise ValueError("JWT Secret Key not found in Parameter Store")
'''

app = Flask(__name__)
with open('flask_app_jwt_configuration.json') as config_file:
    config_data = json.load(config_file)
    logger.debug(config_data)
app.config["DEBUG"] = True
app.config['sftp_hostname'] = env
app.config['kms_key_id'] = kms_key_id
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024    # 100 Mb limit
CORS(app, supports_credentials=True)
app.config['JWT_TOKEN_LOCATION'] = config_data['JWT_TOKEN_LOCATION']
# Set the cookie paths, so that you are only sending your access token
# cookie to the access endpoints, and only sending your refresh token
# to the refresh endpoint.
app.config['JWT_ACCESS_COOKIE_PATH'] = config_data['JWT_ACCESS_COOKIE_PATH']
app.config['JWT_REFRESH_COOKIE_PATH'] = config_data['JWT_REFRESH_COOKIE_PATH']
app.config['JWT_COOKIE_CSRF_PROTECT'] = config_data['JWT_COOKIE_CSRF_PROTECT']
app.config['JWT_CSRF_IN_COOKIES'] = config_data['JWT_CSRF_IN_COOKIES']
app.config['JWT_COOKIE_DOMAIN'] = config_data['JWT_COOKIE_DOMAIN'] # e.g. mycompanydomain.com
app.config['front_end_CORS_origin'] = config_data['front_end_CORS_origin']      # e.g. https://ui.mycompanydomain.com
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config_data['JWT_ACCESS_TOKEN_EXPIRES']
# Set the secret key to sign the JWTs with
app.config['JWT_SECRET_KEY'] = jwt_secret_key
app.config['JWT_COOKIE_SAMESITE'] = config_data['JWT_COOKIE_SAMESITE']
app.config['JWT_COOKIE_SECURE'] = config_data['JWT_COOKIE_SECURE']
logger.debug(app.config)
jwt = JWTManager(app)
cw = boto3.client('cloudwatch')
# Get gunicorn worker process PID for logging
pid = os.getpid()

# Get Fargate Task ARN
fargate_task_metadata_path =  os.getenv('ECS_CONTAINER_METADATA_URI_V4')
resp = requests.get(fargate_task_metadata_path + "/task").json()
fargate_task_arn = resp.get('TaskARN')
fargate_task_id = fargate_task_arn.split("/")[2]
cluster_arn = resp.get('Cluster')

@app.route('/healthcheck', methods=['GET',])
def health_check():
    response = jsonify({'message': "Health check executed."})
    response.status_code = 200

    fargate_ephemeral_space = psutil.disk_usage('/var/sftp-upload-scratch-space').free
    logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - health_check(): fargate task total space:: {fargate_ephemeral_space}')

    Dimension = {
        'Name': 'Fargate_Task',
        'Value': fargate_task_arn
    }

    cw_args = {
        'Namespace': 'ECS',
        'MetricData': [
            {
                'MetricName': 'Fargate Task Ephemeral Storage',
                'Dimensions': [Dimension],
                'Value': fargate_ephemeral_space,
                'Unit': 'Count',
                'StorageResolution': 1
            }
        ]
    }
    try:
        cw_resp = cw.put_metric_data(**cw_args)
        logger.debug(f': {fargate_task_id}(PID:{pid}) - health_check(): finished writing metric data: {cw_resp}')
        return response
    except Exception as e:
        logger.error(f'TaskID: {fargate_task_id}(PID:{pid}) - health_check(): call to /health_check returned exception {e}')
        return bad_request("Bad or Invalid Request", 500)  # Internal Server Error

@app.route('/api/isconnected', methods=['GET',])
@jwt_required
def isconnected():
    response = jsonify({'message': "API is connected."})
    # logger.debug(f'isconnected(): response: {response}')
    response.status_code = 200

    return response

@app.route('/api/authenticate', methods=['POST', 'OPTIONS'])
@crossdomain(origin=app.config['front_end_CORS_origin'])
def authenticate():
    try:
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - authenticate(): Request received')
        sftp_hostname = app.config.get('sftp_hostname')
        usr, passwdorpkey = authenticate_request(request)

        sftp_connection = create_sftp_connection(usr, passwdorpkey, sftp_hostname)
        res = type(sftp_connection).__name__

        if res == 'SFTPClient':
            response = jsonify({'message': "Authentication successful."})

            cred = encrypt_username_password_boto(usr + " " + passwdorpkey, kms_key_id)
            access_token = create_access_token(identity=cred)

            # We still need to call these functions to set the
            # JWTs in the cookies
            jwt_exp_time_config = app.config.get('JWT_ACCESS_TOKEN_EXPIRES')
            set_access_cookies(response, access_token, jwt_exp_time_config)

            response.status_code = 200
            logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - authenticate(): Returning with 200 status code')

            return response

        elif res == 'AuthenticationException':
            response = jsonify({'message': "Authentication Failed"})
            response.status_code = 401
            logger.error(f'TaskID: {fargate_task_id}(PID:{pid}) - authenticate(): Authentication Failure. Returning with 401 status code')
            return response
        else:
            response = jsonify({'message': "Network/Socket Error occurred while making connection to SFTP endpoint"})
            response.status_code = 500  # Internal Server Error
            logger.error(f'TaskID: {fargate_task_id}(PID:{pid}) - authenticate(): Returning with 500 status code')
            return response

    except Exception as e:
        logger.error(f'TaskID: {fargate_task_id}(PID:{pid}) - authenticate(): call to /api/authenticate returned exception {e}')
        return bad_request("Bad or Invalid Request", 500)  # Internal Server Error

@app.after_request
def refresh_expiring_jwts(response):
    try:
        request_str = str(request)
        allowed_endpoints = ["listchildnodes", "numberofchildnodes", "upload", "download", "delete", "rename", "createfolder"]

        # Only create access tokens for specific endpoints
        if any(item in request_str for item in allowed_endpoints):
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - refresh_expiring_jwts(): {request_str}')
            exp_timestamp = get_raw_jwt()["exp"]
            now = datetime.datetime.now(timezone.utc)
            target_timestamp = datetime.datetime.timestamp(now + timedelta(seconds=120))
            if target_timestamp > exp_timestamp:
                logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - refresh_expiring_jwts(): Setting new access token')
                jwt_exp_time_config = app.config.get('JWT_ACCESS_TOKEN_EXPIRES')
                access_token = create_access_token(identity=get_jwt_identity())
                set_access_cookies(response, access_token, jwt_exp_time_config)
            else:
                logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - refresh_expiring_jwts(): Target expiration time is not within the 2 mins of original expiration time')
        return response
    except (RuntimeError,KeyError):
        # Case where there is not a valid JWT. Just return the original respone
        logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - refresh_expiring_jwts(): In EXCEPT CLAUSE')
        return response

@app.route('/api/logout', methods=['POST'])
@jwt_required
def logout():
    try:
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - logout(): Request received')
        response = jsonify({'logout': True})
        response.status_code = 200
        # The following call does both, unset_access_cookies as well as unset_refresh_cookies
        unset_jwt_cookies(response)
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - logout(): Responding back with 200 status code')
        return response

    except Exception as e:
        logger.error(f'TaskID: {fargate_task_id}(PID:{pid}) - logout(): call to /api/logout returned exception {e}')
        return bad_request("Bad or Invalid Request",500)


@app.route('/api/listchildnodes', methods=['POST'])
@jwt_required
def list_child_nodes():
    try:
        
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - list_child_nodes(): Request received')
        sftp_hostname = app.config.get('sftp_hostname')
        usr, passwdorpkey = authenticate_request(request)
        
        response_body = {}

        request_data = request.get_json()
        node_name = request_data['node_name']  # what is parent node
        node_type = request_data['node_type']  # do we want folders or non-folders
        response_body['data'] = []

        sftp_connection = get_sftp_connection(usr, passwdorpkey, sftp_hostname)
        nodes = sftp_connection.listdir_attr(node_name)

        for node in nodes:
            if node_type == "folder" and node.longname[:1] == "d":  # if folder node
                response_body['data'].append(
                    {
                        'label': node.filename,
                        'data': node_name + "/" + node.filename,
                        'leaf': False,
                        'key': node_name + "/" + node.filename,  # for react js
                    }
                )
            elif node_type == "file" and node.longname[:1] == "-":

                file_ext = "n/a"

                # find last "." in file name
                file_name_split = node.filename.rsplit(".", 1)

                if len(file_name_split) == 2:  # if we have 2 items come back the last is the extension.
                    file_ext = file_name_split[1]

                response_body['data'].append(
                    {
                        'name': node.filename,
                        'data': node_name + "/" + node.filename,
                        'leaf': True,
                        'type': file_ext,
                        'size': round(node.st_size/1024, 2),
                        'last_accessed_on': datetime.datetime.fromtimestamp(node.st_atime).strftime('%Y-%m-%d %H:%M:%S'),
                        'last_modified_on': datetime.datetime.fromtimestamp(node.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    }
                )
        response = jsonify(response_body)
        response.status_code = 200
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - list_child_nodes(): Responding back with 200 status code')
        return response

    except Exception as e:
        logger.error(f'TaskID: {fargate_task_id}(PID:{pid}) - list_child_nodes(): call to /api/listchildnodes returned exception {e}')
        return bad_request("Bad or Invalid Request", 500)

@app.route('/api/numberofchildnodes', methods=['POST'])
@jwt_required
def number_of_child_nodes():
    try:
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - number_of_child_nodes(): Request received')
        sftp_hostname = app.config.get('sftp_hostname')
        usr, passwdorpkey = authenticate_request(request)
        response_body = {}

        request_data = request.get_json()
        node_name = request_data['node_name']  # what is parent node
        response_body['data'] = []

        sftp_connection = get_sftp_connection(usr, passwdorpkey, sftp_hostname)

        nodes = sftp_connection.listdir_attr(node_name)
        number_of_nodes = len(nodes)

        #Return number of files within a folder
        response_body['data'].append(
            {
                'number_of_nodes': number_of_nodes
            }
        )

        response = jsonify(response_body)
        response.status_code = 200
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - number_of_child_nodes(): Responding back with 200 status code')
        return response
    except Exception as e:
        logger.error(f'TaskID: {fargate_task_id}(PID:{pid}) - number_of_child_nodes(): call to /api/numberofchildnodes returned exception {e}')
        return bad_request("Bad or Invalid Request", 500)


# SFTP Upload operation
@app.route('/api/upload', methods=['POST'])
@jwt_required
def upload():
    try:
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): Upload file request received')

        sftp_hostname = app.config.get('sftp_hostname')
        usr, passwd = authenticate_request(request)

        req_form = request.form
        filename = req_form.getlist('file_name')[0]

        filename = replace_forward_slash(filename)

        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): File to be uploaded : {filename}')

        file = request.files.get("filetoupload")
        response_body = {}

        upload_scratch_space_path = '/var/sftp-upload-scratch-space'

        if (os.path.exists(upload_scratch_space_path) == False):
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): upload scratch path {upload_scratch_space_path} does not exist. Creating it ')
            os.mkdir(upload_scratch_space_path)
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): created the {upload_scratch_space_path} path')
        else:
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - upload():upload scratch path {upload_scratch_space_path} exists ')
            listfolders = os.listdir(upload_scratch_space_path)
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - upload():List of existing folders (should be empty) : {listfolders} ')

        # create unique temp path for the file
        temppath = upload_scratch_space_path + '/' + str(uuid.uuid4().hex) + '_' + str(
            datetime.datetime.utcnow().timestamp()).replace('.', '_')
        logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): upload temp path to be created : {temppath}')
        if (os.path.exists(temppath)):
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): upload temp path already exists')
            os.rmdir(temppath)
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): deleted the existing upload temp path')
            os.mkdir(temppath)
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): created the upload temp path again')
        else:
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): upload temp path does not exists. Creating new one')
            os.mkdir(temppath)

        #Saving the file to fargate task scratch space
        file.save(os.path.join(temppath, filename))

        form_data = request.form.to_dict(flat=False)
        file_path = form_data['file_path'][0]
        filetouploadname = file_path + "/" + filename

        #Making SFTP Connection
        sftp_connection = get_sftp_connection(usr, passwd, sftp_hostname)
        #Uploading the file to SFTP endpoint, from fargate task scratch space
        logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): Uploading the file to SFTP endpoint, from fargate task scratch space')
        upload_file_response = sftp_connection.put(os.path.join(temppath, filename), filetouploadname)

        # Remove the temp path and the file from the local storage after it is uploaded to the SFTP endpoint
        logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): file uploaded to the SFTP server')
        os.remove(os.path.join(temppath, filename))
        logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): upload temp path file deleted')
        os.rmdir(temppath)
        logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): upload temp path deleted')

        response_body['file_permission'] = str(upload_file_response)
        response_body['message'] = "File uploaded successfully."

        response = jsonify(response_body)
        response.status_code = 200
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): Responding back with 200 status code')
        return response

    except Exception as e:
        logger.error(f'TaskID: {fargate_task_id}(PID:{pid}) - upload(): call to /api/upload returned exception {e}')
        return bad_request(e.description, 500)

@app.route('/api/download', methods=['POST'])
@jwt_required
def download():
    try:
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): Request received')
        sftp_hostname = app.config.get('sftp_hostname')
        usr, passwd = authenticate_request(request)

        request_data = request.get_json()

        filepath = request_data['path']
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): File Path: {filepath}')
        filename = str(filepath).split('/')[-1]  # Returns the filename

        sftp_connection = get_sftp_connection(usr, passwd, sftp_hostname)
        download_scratch_space_path = '/var/sftp-download-scratch-space'

        if (os.path.exists(download_scratch_space_path) == False):
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): download scratch path {download_scratch_space_path} does not exist. Creating it ')
            os.mkdir(download_scratch_space_path)
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): created the {download_scratch_space_path} path')
        else:
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): download scratch path {download_scratch_space_path} exists ')
            listfolders = os.listdir(download_scratch_space_path)
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): List of existing folders (should be empty) : {listfolders} ')

        # create unique temp path for the file
        temppath = download_scratch_space_path + '/' + str(uuid.uuid4().hex) + '_' + str(
            datetime.datetime.utcnow().timestamp()).replace('.', '_')
        logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): temp path to be created : {temppath}')
        if (os.path.exists(temppath)):
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): download temp path already exists')
            os.rmdir(temppath)
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): deleted the existing download temp path')
            os.mkdir(temppath)
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): created the download temp path again')
        else:
            logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): download temp path does not exists. Creating new one')
            os.mkdir(temppath)

        remote_path = filepath
        local_path = temppath + "/" + filename
        # Getting file from SFTP endpoint
        sftp_connection.get(remote_path, local_path, callback=None)

        logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): sending file : remote path: {remote_path} local_path: {local_path}')

        # Remove the temp path and the file from the local storage after it is sent to the client
        @after_this_request
        def remove_temp_path(response):
            try:
                os.remove(local_path)
                os.rmdir(temppath)
                logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): removed temp path after_this_request')
            except Exception as e:
                logger.error(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): Download operation after_this_request error occurred : {e}')
                return bad_request(e, 500)
            return response

        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): Responding back with 200 status code')
        return send_file(local_path, as_attachment=True, attachment_filename=filename)

    except Exception as e:
        logger.error(f'TaskID: {fargate_task_id}(PID:{pid}) - download(): call to /api/download returned exception {e}')
        return bad_request("Bad or Invalid Request", 500)

@app.route('/api/delete', methods=['POST'])
@jwt_required
def delete():
    try:
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - delete(): Request received')
        sftp_hostname = app.config.get('sftp_hostname')
        usr, passwd = authenticate_request(request)

        response_body = {}

        request_data = request.get_json()
        node_name = request_data['node_name']  # path
        node_type = request_data['node_type']  # do we want folders or non-folders

        sftp_connection = get_sftp_connection(usr, passwd, sftp_hostname)

        if node_type == "folder":
            sftp_connection.rmdir(node_name)
            logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - delete(): Folder {node_name} deleted successfully')
            response_body['message'] = "Folder deleted successfully."

        elif node_type == "file":
            rmfile = sftp_connection.remove(node_name)
            logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - delete(): File {node_name} deleted successfully')
            response_body['message'] = "File deleted successfully."

        response = jsonify(response_body)
        response.status_code = 200
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - delete(): Responding back with 200 status code')
        return response

    except Exception as e:
        logger.error(f'TaskID: {fargate_task_id}(PID:{pid}) - delete(): call to /api/delete returned exception {e}')
        return bad_request("Bad or Invalid Request", 500)

@app.route('/api/rename', methods=['POST'])
@jwt_required
def rename():
    try:
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - rename(): Request received')
        sftp_hostname = app.config.get('sftp_hostname')
        usr, passwd = authenticate_request(request)

        response_body = {}
        request_data = request.get_json()
        node_type = request_data['node_type']
        current_path = request_data['current_path']
        new_path = request_data['new_path']
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - rename(): Current Path: {current_path}')
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - rename(): New Path: {new_path}')

        if new_path != current_path:
            if node_type == "folder":
                logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - rename(): Cannot rename a folder')
                return bad_request(f'Cannot rename a folder', 500)  # cant rename a directory
            elif node_type == "file":

                if contains_special_characters(request_data['file_name']):
                    return bad_request("Name contains special characters.", 400)

                sftp_connection = get_sftp_connection(usr, passwd, sftp_hostname)
                sftp_connection.rename(current_path,new_path)
                response_body['message'] = "File renamed successfully."
                response_body['new_path'] = new_path
                response_body['new_name'] = new_path[new_path.rfind('/')+1:]
                logger.debug(f'TaskID: {fargate_task_id}(PID:{pid}) - rename(): File renamed successfully.')

                response = jsonify(response_body)
                response.status_code = 200
                logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - rename(): Responding back with 200 status code')
            else:
                logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - rename(): Bad Input')
                return bad_request(f'Bad Input', 500)
        else:
            response = jsonify("No name change detected.")
            logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - rename(): No name change detected')
            response.status_code = 200

        return response

    except Exception as e:
        logger.error(f'TaskID: {fargate_task_id}(PID:{pid}) - rename(): call to /api/rename returned exception {e}')
        return bad_request("Bad or Invalid Request", 500)


@app.route('/api/createfolder', methods=['POST'])
@jwt_required
def create_folder():
    try:
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - create_folder(): Request received')
        sftp_hostname = app.config.get('sftp_hostname')
        usr, passwd = authenticate_request(request)

        response_body = {}

        request_data = request.get_json()
        node_type = request_data['node_type']
        new_folder_path = request_data['new_node_path']

        if contains_special_characters(request_data['node_name']):
            return bad_request("Name contains special characters.", 400)

        if node_type == "folder":
            sftp_connection = get_sftp_connection(usr, passwd, sftp_hostname)

            sftp_connection.mkdir(new_folder_path, 511)
            logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - create_folder(): New folder at {new_folder_path} created successfully ')
            response_body['message'] = "Folder created successfully."

        response = jsonify(response_body)
        response.status_code = 200
        logger.info(f'TaskID: {fargate_task_id}(PID:{pid}) - create_folder(): Responding back with 200 status code')
        return response

    except Exception as e:
        logger.error(f'TaskID: {fargate_task_id}(PID:{pid}) - create_folder(): call to /api/create_folder returned exception {e}')
        return bad_request("Bad or Invalid Request", 500)


@app.errorhandler(400)
def bad_request(error=None, status=None):
    message = {
        'status': status,
        'message': 'Invalid request: ' + str(error)
    }
    resp = jsonify(message)
    resp.status_code = status

    return resp


@app.errorhandler(500)
def internal_error(error=None):
    message = {
        'status': 500,
        'message': 'Internal server error: ' + error
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8042)
