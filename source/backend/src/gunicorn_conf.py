#To disguise Server Name/Version in HTTP Header
import gunicorn
gunicorn.SERVER_SOFTWARE = "WEBSERVER"

