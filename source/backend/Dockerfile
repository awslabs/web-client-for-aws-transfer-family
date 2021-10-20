# https://pythonspeed.com/articles/multi-stage-docker-python/
# Use an official Python runtime as a parent image
FROM python:3.8.1 AS builder

# setting environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN pip3 install --user -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# second unnamed stage
FROM python:3.8-slim
COPY --from=builder /root/.local /root/.local
# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

# Set the working directory to /app
WORKDIR /app
COPY ./src /app

#Setting SFTP Endpoint as environment variables
ENV sftp_hostname=${sftp_hostname}
ENV kms_arn=${kms_arn}
RUN echo "SFTP endpoint: $sftp_hostname"

#Setting KMS Key ID as environment variables
ENV kms_key_id=${kms_key_id}
RUN echo "KMS Key ID: $kms_key_id"

#Setting JWT Secret Key Parameter value as environment variables
ENV jwt_secret_key_parameter_value=${jwt_secret_key_parameter_value}
RUN echo "JWT Secret Key Parameter value: $jwt_secret_key_parameter_value"

#Setting Gunicon number of workers as environment variables
ENV workers=${workers}
RUN echo "Number of Gunicorn Workers: $workers" # TODO: Implement it

#Entrypoint
ENTRYPOINT gunicorn --bind 0.0.0.0:80 --config gunicorn_conf.py transfer_sftp_backend:app --workers=3 --timeout 600