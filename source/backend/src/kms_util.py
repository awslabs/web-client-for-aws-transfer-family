import boto3
import base64
import logging
import logging.config
from botocore.exceptions import ClientError
from botocore.config import Config

config = Config(
   retries = {
      'max_attempts': 10,
      'mode': 'standard'
   }
)
session = boto3.session.Session()
kms = session.client('kms', config=config)

logging.config.fileConfig('logging.conf')
# create logger
logger = logging.getLogger('kmsutil')

def encrypt_username_password_boto(usrpwd, kms_key_id):
    try:
        stuff = kms.encrypt(KeyId=kms_key_id, Plaintext=usrpwd)
        binary_encrypted = stuff[u'CiphertextBlob']
        encrypted_password = base64.b64encode(binary_encrypted)
        return encrypted_password.decode()

    except ClientError as e:
        logger.error(f'encrypt_username_password_boto(): exception --> {e}')
        return None, None

def decrypt_username_password_boto(encrypted_userpwd):
    try:
        binary_data = base64.b64decode(encrypted_userpwd)
        meta = kms.decrypt(CiphertextBlob=binary_data)
        plaintext = meta[u'Plaintext']
        return plaintext.decode()

    except ClientError as e:
        logger.error(f'decrypt_username_password_boto(): exception --> {e}')
        return None, None


