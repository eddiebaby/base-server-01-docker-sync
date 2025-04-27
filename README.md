# Base Server 01 Docker Synchronization

This repository contains scripts and utilities for synchronizing Docker environments for Base Server 01 across multiple machines.

## Purpose

The Docker synchronization setup allows you to maintain identical Docker environments across multiple machines. This is particularly useful for development, testing, and deployment scenarios where consistency is critical.

## Included Scripts

1. **sync_docker_env.bat**
   - Batch file for Docker environment synchronization
   - Provides a menu-driven interface
   - Includes all synchronization operations
   - Works on Windows without PowerShell requirements

2. **docker_sync_quickstart.ps1**
   - Quick start PowerShell script for Docker synchronization
   - Simplified interface for common operations
   - Ideal for users who need a straightforward approach
   - Includes default settings for Base Server 01

3. **create_sync_package.ps1**
   - PowerShell script to create a complete synchronization package
   - Bundles all necessary files for easy distribution
   - Includes image saving and file copying with progress indication
   - Creates a README and ZIP archive for distribution

## Getting Started

### Source Machine (Saving)

1. Run `sync_docker_env.bat` or use PowerShell to run `docker_sync_quickstart.ps1`
2. Choose the option to save the Docker image
3. Specify the image name (default: base_server_01)
4. Specify the output path for the image file
5. Wait for the image to be saved

### Target Machine (Loading)

1. Copy the image file to the target machine
2. Run `sync_docker_env.bat` or use PowerShell to run `docker_sync_quickstart.ps1`
3. Choose the option to load the Docker image
4. Specify the path to the image file
5. Wait for the image to be loaded
6. Create and start a container from the image

## Documentation

For more detailed information, refer to the `Base_Server_01_Sync_Summary.md` file included in this repository.

## Requirements

- Windows 10/11
- Docker Desktop installed and running
- PowerShell 5.1 or later (for PowerShell scripts)
- Administrator privileges (for enabling remote access)

## License

This project is licensed under the MIT License - see the LICENSE file for details.