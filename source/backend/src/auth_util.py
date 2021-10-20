import base64
import logging
import logging.config
from flask_jwt_extended import ( decode_token, get_jwt_identity )
from kms_util import decrypt_username_password_boto

logging.config.fileConfig('logging.conf')
# create logger
logger = logging.getLogger('authutillogger')

# Used to authenticate each request. This method handles
def authenticate_request(request):
    try:
        # Only first request would have Authorization header
        if(request.headers.has_key('Authorization')):
            logger.debug(f'authenticate_request(): first request - basic authentication')
            auth = request.headers.get('Authorization')
            authDetails = str(auth).split()
            authMethod = authDetails[0] # should be Basic or Bearer

            if authMethod == "Basic":
                credentials = authDetails[1]
                # base64 decode
                decodedcred = base64.b64decode(credentials).decode('utf-8')  # to remove b' ' from the string
                usr = decodedcred.split(" ")[0]
                passwdorpkey = decodedcred.split(" ")[1]
        else:

            # NOTE - you can uncomment for debugging purposes but this will log sensitive data
            # logger.debug(f'authenticate_request(): Second request {get_jwt_identity()}')

            # decode our token which also validates token
            #decoded_token = decode_token(request.cookies.get("access_token_cookie"))

            decrypted_usrpwd = decrypt_username_password_boto(get_jwt_identity())

            # NOTE - you can uncomment for debugging purposes but this will log sensitive data
            # logger.debug(f'decrypted_usrpwd {decrypted_usrpwd}')

            # grab identity
            credentials = decrypted_usrpwd.split(" ")

            usr = credentials[0]
            passwdorpkey = credentials[1]

        return usr, passwdorpkey
    except Exception as e:
        logger.error(f'authenticate_request(): Error -  {e}')
        return e