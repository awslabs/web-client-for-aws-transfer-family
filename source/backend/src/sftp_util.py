import paramiko
import logging
import logging.config
from cachetools import cached, TTLCache

logging.config.fileConfig('logging.conf')
# create logger
logger = logging.getLogger('sftputillogger')

sftpConnections = {}
channeltimeout = 120  # in seconds

# Create SFTP Connection for a given user
def create_sftp_connection(username, userpass, sftp_hostname):
    try:
        transport = paramiko.Transport((sftp_hostname, 22))
        transport.connect(username=username, password=userpass)

        sftp_conn = paramiko.SFTPClient.from_transport(transport)
        sftp_conn.get_channel().settimeout(channeltimeout)
        return sftp_conn
    except Exception as e:
        logger.error(f'create_sftp_connection(): An error occurred creating SFTP client connection --> {e}')
        return e

# Get SFTP Connection for a given user,
# either from the cache or create a new connection
@cached(cache=TTLCache(maxsize=1024, ttl=channeltimeout))
def get_sftp_connection(usr, passwdorpkey, sftp_hostname):
     try:
         logger.debug(f'get_sftp_connection(): Creating new sftp connection')
         sftp_conn = create_sftp_connection(usr, passwdorpkey, sftp_hostname)
         return sftp_conn
     except Exception as e:
         logger.error(f'get_sftp_connection(): An error occurred creating SFTP client --> {e}')
         return e
