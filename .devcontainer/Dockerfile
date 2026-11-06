# This image has Selenium and the Chrome driver already installed
FROM rofrano/pipeline-selenium:sp26

ARG USERNAME=vscode
USER root

# Set up the Python development environment
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN python -m pip install --upgrade pip pipenv && \
    pipenv install --system --dev

# Configuring insecure Docker registry
COPY config/insecure-registry.json /etc/docker/daemon.json 

# Become a regular user for development
USER $USERNAME

# Install user mode tools
COPY .devcontainer/scripts/install-tools.sh /tmp/
RUN cd /tmp && bash ./install-tools.sh
