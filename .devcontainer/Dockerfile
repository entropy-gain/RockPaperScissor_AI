FROM mcr.microsoft.com/devcontainers/python:3.10

ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    curl \
    git \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip

# Setup AWS CLI for local DynamoDB
RUN mkdir -p /root/.aws
RUN echo "[default]\nregion = us-east-1\naws_access_key_id = dummy\naws_secret_access_key = dummy" > /root/.aws/credentials
RUN echo "[default]\nregion = us-east-1" > /root/.aws/config

# Install useful Python packages globally
RUN pip install --no-cache-dir black isort pytest pytest-cov pylint mypy boto3 mangum fastapi uvicorn

# Create non-root user with sudo access
RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid 1000 -m vscode \
    && apt-get update \
    && apt-get install -y sudo \
    && echo vscode ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode

# Configure Poetry for non-root user
USER vscode
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/home/vscode/.local/bin:$PATH"
RUN poetry config virtualenvs.in-project true

# Switch back to root for permissions
USER root

# Create workspace directory with correct permissions
RUN mkdir -p /workspace && chown vscode:vscode /workspace

WORKDIR /workspace