# Docker Sync Quick Start
# This script provides a quick start for Docker synchronization

# Function to display a header
function Show-Header {
    param (
        [string]$title
    )
    
    Write-Host
    Write-Host "===== $title =====" -ForegroundColor Cyan
    Write-Host
}

# Function to check if Docker is running
function Test-DockerRunning {
    try {
        $null = docker info 2>&1
        return $true
    }
    catch {
        return $false
    }
}

# Function to check if a file exists
function Test-FileExists {
    param (
        [string]$path
    )
    
    return Test-Path $path
}

# Function to save Docker image
function Save-DockerImage {
    param (
        [string]$imageName,
        [string]$outputPath
    )
    
    try {
        Write-Host "Saving image '$imageName' to '$outputPath'..." -ForegroundColor Yellow
        Write-Host "This may take several minutes. Please wait..." -ForegroundColor Yellow
        
        docker save -o $outputPath $imageName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Image saved successfully." -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "Failed to save image. Exit code: $LASTEXITCODE" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "Error saving image: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to load Docker image
function Load-DockerImage {
    param (
        [string]$inputPath
    )
    
    try {
        Write-Host "Loading image from '$inputPath'..." -ForegroundColor Yellow
        Write-Host "This may take several minutes. Please wait..." -ForegroundColor Yellow
        
        docker load -i $inputPath
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Image loaded successfully." -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "Failed to load image. Exit code: $LASTEXITCODE" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "Error loading image: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to create container from image
function New-DockerContainer {
    param (
        [string]$imageName,
        [string]$containerName,
        [int]$hostPort = 5001,
        [int]$containerPort = 5000
    )
    
    try {
        # Check if container already exists
        $containerExists = docker ps -a --filter "name=$containerName" -q
        
        if ($null -ne $containerExists -and $containerExists -ne "") {
            Write-Host "Container '$containerName' already exists." -ForegroundColor Yellow
            
            $removeContainer = Read-Host "Do you want to remove it and create a new one? (y/n)"
            
            if ($removeContainer -eq "y") {
                Write-Host "Removing container '$containerName'..." -ForegroundColor Yellow
                docker rm -f $containerName | Out-Null
                
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "Failed to remove container. Exit code: $LASTEXITCODE" -ForegroundColor Red
                    return $false
                }
            }
            else {
                Write-Host "Container creation aborted." -ForegroundColor Yellow
                return $false
            }
        }
        
        Write-Host "Creating container '$containerName' from image '$imageName'..." -ForegroundColor Yellow
        docker create -p ${hostPort}:${containerPort} --name $containerName $imageName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Container created successfully." -ForegroundColor Green
            
            $startContainer = Read-Host "Do you want to start the container? (y/n)"
            
            if ($startContainer -eq "y") {
                Write-Host "Starting container '$containerName'..." -ForegroundColor Yellow
                docker start $containerName
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "Container started successfully." -ForegroundColor Green
                    return $true
                }
                else {
                    Write-Host "Failed to start container. Exit code: $LASTEXITCODE" -ForegroundColor Red
                    return $false
                }
            }
            
            return $true
        }
        else {
            Write-Host "Failed to create container. Exit code: $LASTEXITCODE" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "Error creating container: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to run Docker Sync Quick Start
function Start-DockerSyncQuickStart {
    # Display header
    Clear-Host
    Show-Header "Docker Sync Quick Start"
    
    # Check if Docker is running
    if (-not (Test-DockerRunning)) {
        Write-Host "Error: Docker is not running or not installed." -ForegroundColor Red
        Write-Host "Please start Docker Desktop and try again." -ForegroundColor Red
        return $false
    }
    
    # Display menu
    Write-Host "1. Save Docker image (on source machine)" -ForegroundColor Yellow
    Write-Host "2. Load Docker image (on target machine)" -ForegroundColor Yellow
    Write-Host "3. Create and start container (on target machine)" -ForegroundColor Yellow
    Write-Host "4. Exit" -ForegroundColor Yellow
    Write-Host
    
    $choice = Read-Host "Enter your choice (1-4)"
    
    switch ($choice) {
        "1" {
            # Save Docker image
            $imageName = Read-Host "Enter the image name (default: base_server_01)"
            
            if ([string]::IsNullOrWhiteSpace($imageName)) {
                $imageName = "base_server_01"
            }
            
            $outputPath = Read-Host "Enter the path to save the image file (default: ./base_server_01-image.tar)"
            
            if ([string]::IsNullOrWhiteSpace($outputPath)) {
                $outputPath = "./base_server_01-image.tar"
            }
            
            Save-DockerImage -imageName $imageName -outputPath $outputPath
        }
        "2" {
            # Load Docker image
            $inputPath = Read-Host "Enter the path to the image file (default: ./base_server_01-image.tar)"
            
            if ([string]::IsNullOrWhiteSpace($inputPath)) {
                $inputPath = "./base_server_01-image.tar"
            }
            
            if (-not (Test-FileExists $inputPath)) {
                Write-Host "Error: File '$inputPath' does not exist." -ForegroundColor Red
                return $false
            }
            
            Load-DockerImage -inputPath $inputPath
        }
        "3" {
            # Create and start container
            $imageName = Read-Host "Enter the image name (default: base_server_01)"
            
            if ([string]::IsNullOrWhiteSpace($imageName)) {
                $imageName = "base_server_01"
            }
            
            $containerName = Read-Host "Enter the container name (default: base_server_01_instance)"
            
            if ([string]::IsNullOrWhiteSpace($containerName)) {
                $containerName = "base_server_01_instance"
            }
            
            $hostPortInput = Read-Host "Enter the host port (default: 5001)"
            $hostPort = 5001
            
            if (-not [string]::IsNullOrWhiteSpace($hostPortInput) -and $hostPortInput -match "^\d+$") {
                $hostPort = [int]$hostPortInput
            }
            
            $containerPortInput = Read-Host "Enter the container port (default: 5000)"
            $containerPort = 5000
            
            if (-not [string]::IsNullOrWhiteSpace($containerPortInput) -and $containerPortInput -match "^\d+$") {
                $containerPort = [int]$containerPortInput
            }
            
            New-DockerContainer -imageName $imageName -containerName $containerName -hostPort $hostPort -containerPort $containerPort
        }
        "4" {
            # Exit
            Write-Host "Exiting..." -ForegroundColor Yellow
            return $true
        }
        default {
            Write-Host "Invalid choice. Please try again." -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Run the main function
Start-DockerSyncQuickStart