# Multi-language Development Container
# Following :ContainerizationPattern for Python, C++, JavaScript, and C# support
# :Context: Project primarily Python-based with Flask, SQL database, and market data collection

# Start with Python official image as the base
FROM python:latest

# Set environment variables to avoid prompts during installation
# :EnvironmentConfiguration for non-interactive setup
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NODE_VERSION=20.x \
    # Set locale
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Set working directory
WORKDIR /app

# Install system dependencies and tools
# :DependencyManagement for system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required build tools and libraries
    build-essential \
    cmake \
    ca-certificates \
    curl \
    git \
    wget \
    gnupg \
    lsb-release \
    # C++ development tools
    g++ \
    gdb \
    # SQL support
    sqlite3 \
    libsqlite3-dev \
    # Clean up to reduce image size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install JavaScript environment (Node.js and npm)
# :TechnologyVersion for JavaScript
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION} | bash - \
    && apt-get update \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g npm@latest

# Install C# support (optional)
# :TechnologyVersion for C#
RUN wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    dotnet-sdk-7.0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# :DependencyManagement for Python packages
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    # Flask specific installation
    && pip install --no-cache-dir flask flask-sqlalchemy

# Set up volume mapping for data persistence
# :VolumeMapping for project data and database files
VOLUME ["/app/data", "/app/db"]

# Environment variables to address :CompatibilityIssue between language runtimes
# Ensure each language has its own environment variables properly configured
ENV PATH="/app/node_modules/.bin:${PATH}" \
    DOTNET_ROOT="/usr/share/dotnet" \
    PYTHONPATH="/app:${PYTHONPATH}"

# Expose ports for development services
# Flask default port
EXPOSE 5000
# Additional ports for other services
EXPOSE 8000 8080

# Set development-specific environment variables
# :EnvironmentConfiguration for development mode
ENV FLASK_ENV=development \
    FLASK_DEBUG=1 \
    PYTHONUNBUFFERED=1

# Set entrypoint to keep container running in development mode
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["echo 'Multi-language development container started.' && tail -f /dev/null"]

# Development setup instructions
# 1. Build: docker build -t multi-dev-container .
# 2. Run: docker run -it --name dev-env -v $(pwd):/app -p 5000:5000 multi-dev-container
# 3. For interactive use: docker exec -it dev-env bash