FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    curl \
    git \
    wget \
    zip \
    unzip \
    jq \
    vim \
    htop \
    tree \
    ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip

# Install actionlint for GitHub Actions validation
RUN wget https://github.com/rhysd/actionlint/releases/download/v1.7.5/actionlint_1.7.5_linux_amd64.tar.gz \
    && tar -xzf actionlint_1.7.5_linux_amd64.tar.gz \
    && mv actionlint /usr/local/bin/ \
    && rm actionlint_1.7.5_linux_amd64.tar.gz

# Set up vscode user with sudo
RUN useradd -m -s /bin/bash vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode

# Set working directory
WORKDIR /home/vscode

USER vscode
