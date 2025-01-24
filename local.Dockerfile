FROM docker.io/dataloopai/dtlpy-agent:cpu.py3.10.opencv

USER root

# Install required packages
RUN apt-get update && apt-get install -y \
    curl \
    nginx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm@latest

# Generate SSL certificate
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/local.dataloop.ai.key \
    -out /etc/ssl/certs/local.dataloop.ai.crt \
    -subj "/CN=local.dataloop.ai"

# Copy application files
WORKDIR /tmp/app
COPY requirements.txt /tmp/app

# Install Python dependencies
RUN pip install --user -r /tmp/app/requirements.txt

