# Multi-Language Development Container

This repository contains a Docker-based development environment configured for multi-language development following the `:ContainerizationPattern`. The setup provides a consistent development environment with support for Python, C++, JavaScript, and C#.

## Technology Versions

The container includes the following technology versions:
- **Python**: Latest stable version with Flask support
- **C++**: GCC/G++ compiler suite with build essentials
- **JavaScript**: Node.js latest LTS with npm
- **C#**: .NET SDK 7.0 (optional support)

## Context

This development container is designed for a project that is primarily Python-based with Flask for web components, SQL database for data storage, and market data collection functionality.

## Features

- **`:ContainerizationPattern`**: Isolated, reproducible development environment
- **`:EnvironmentConfiguration`**: Pre-configured for development with debug enabled
- **`:DependencyManagement`**: Python packages, system libraries, and development tools
- **`:VolumeMapping`**: Data persistence for database files and market data
- **`:CompatibilityIssue`** mitigation between language runtimes

## Getting Started

### Prerequisites

- Docker installed on your host machine
- Docker Compose installed on your host machine

### Building and Running

1. **Build and start the container**:
   ```bash
   docker-compose up -d
   ```

2. **Access the container shell**:
   ```bash
   docker exec -it multi-lang-dev bash
   ```

3. **Stop the container**:
   ```bash
   docker-compose down
   ```

## Volume Mapping

The Docker Compose configuration sets up several volumes for data persistence:

- **Project files**: The entire project directory is mounted to `/app` inside the container
- **Database files**: Persistent volume at `/app/db`
- **Market data**: Persistent volume at `/app/data/market`
- **Pip cache**: Caches pip packages to speed up rebuilds

## Development Workflow

1. **Edit code on your host machine** using your preferred IDE/editor
2. **Run and test inside the container** - changes are immediately available
3. **Install additional dependencies** by updating the Dockerfile or requirements.txt and rebuilding

## Addressing Compatibility Issues

This container configuration addresses several potential compatibility issues:

1. **Environment variables**: Each language has specific environment variables configured
2. **Path settings**: Ensures executables from different languages are available
3. **Library conflicts**: Uses isolated package managers for each language
4. **File permissions**: Volume mappings preserve appropriate permissions

## Additional Configuration

### Adding Python Packages

Update the `requirements.txt` file and rebuild the container:

```bash
docker-compose build --no-cache
```

### Adding Node.js Packages

Access the container and use npm:

```bash
docker exec -it multi-lang-dev bash
npm install --save package-name
```

### Configuring C++ Build Environment

The container includes CMake and build essentials. Place your C++ projects in the appropriate directory and build using standard tools.

### Using C# (Optional)

The .NET SDK is available for C# development. Use standard dotnet CLI commands inside the container.

## Troubleshooting

### Container Won't Start

Check Docker logs:
```bash
docker-compose logs
```

### Dependency Installation Issues

If you encounter issues with dependencies, you can modify the Dockerfile and rebuild:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Permission Problems

For permission issues with mounted volumes, ensure your host user has appropriate permissions on the project directory.