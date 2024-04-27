# Base image using Python 3.11.9 on Alpine Linux 3.19
FROM python:3.11.9-alpine3.19

# Set the maintainer label to specify the owner of this Dockerfile
LABEL maintainer="https://github.com/mirzamukkarambaig"

# Environment variable to ensure Python outputs are sent straight to terminal without being buffered
ENV PYTHONUNBUFFERED 1

# Copy the requirements file to the temporary directory in the container
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
# Copy the application directory to the container
COPY ./app /app

# Set the working directory to the app directory inside the container
WORKDIR /app

# Declare the port number the container should expose
EXPOSE 8000

# Switch off the DEV mode by default
ARG DEV=false

# Create a Python virtual environment and install dependencies
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; then \
        /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -rf /tmp/requirements.txt && \
    adduser --disabled-password --no-create-home django-user


# Update PATH environment variable to use binaries from the virtual environment
ENV PATH="/py/bin:$PATH"

# Switch to the non-root user "django-user" for security reasons
USER django-user
