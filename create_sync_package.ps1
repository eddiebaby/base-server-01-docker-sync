# Create Sync Package
# This script creates a package for Docker synchronization

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

# Function to check if a directory exists
function Test-DirectoryExists {
    param (
        [string]$path
    )
    
    return (Test-Path $path) -and (Get-Item $path).PSIsContainer
}

# Function to create a directory if it doesn't exist
function Ensure-DirectoryExists {
    param (
        [string]$path
    )
    
    if (-not (Test-DirectoryExists $path)) {
        try {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
            Write-Host "Created directory: $path" -ForegroundColor Green
            return $true
        }
        catch {
            Write-Host "Error creating directory '$path': $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
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

# Function to copy files with progress
function Copy-FilesWithProgress {
    param (
        [string]$source,
        [string]$destination
    )
    
    try {
        # Get file size
        $fileSize = (Get-Item $source).Length
        $fileSizeMB = [math]::Round($fileSize / 1MB, 2)
        
        Write-Host "Copying file: $source" -ForegroundColor Yellow
        Write-Host "To: $destination" -ForegroundColor Yellow
        Write-Host "File size: $fileSizeMB MB" -ForegroundColor Yellow
        
        # Create a job to copy the file
        $job = Start-Job -ScriptBlock {
            param($src, $dst)
            Copy-Item -Path $src -Destination $dst -Force
        } -ArgumentList $source, $destination
        
        # Wait for the job to complete with progress
        $prevPercent = 0
        
        while ($job.State -eq "Running") {
            if (Test-Path $destination) {
                $destFile = Get-Item $destination
                $copiedSize = $destFile.Length
                $percent = [math]::Min(100, [math]::Round(($copiedSize / $fileSize) * 100))
                
                if ($percent -gt $prevPercent) {
                    Write-Progress -Activity "Copying file" -Status "$percent% Complete" -PercentComplete $percent
                    $prevPercent = $percent
                }
            }
            
            Start-Sleep -Milliseconds 500
        }
        
        # Complete the progress bar
        Write-Progress -Activity "Copying file" -Status "100% Complete" -PercentComplete 100 -Completed
        
        # Get the job result
        $result = Receive-Job -Job $job
        Remove-Job -Job $job
        
        Write-Host "File copied successfully." -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Error copying file: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to create a sync package
function Create-SyncPackage {
    # Display header
    Clear-Host
    Show-Header "Create Docker Sync Package"
    
    # Check if Docker is running
    if (-not (Test-DockerRunning)) {
        Write-Host "Error: Docker is not running or not installed." -ForegroundColor Red
        Write-Host "Please start Docker Desktop and try again." -ForegroundColor Red
        return $false
    }
    
    # Get image name
    $imageName = Read-Host "Enter the image name (default: base_server_01)"
    
    if ([string]::IsNullOrWhiteSpace($imageName)) {
        $imageName = "base_server_01"
    }
    
    # Get output directory
    $outputDir = Read-Host "Enter the output directory for the sync package (default: ./sync_package)"
    
    if ([string]::IsNullOrWhiteSpace($outputDir)) {
        $outputDir = "./sync_package"
    }
    
    # Create output directory
    $dirCreated = Ensure-DirectoryExists -path $outputDir
    
    if (-not $dirCreated) {
        return $false
    }
    
    # Save Docker image
    $imageFile = Join-Path $outputDir "${imageName}-image.tar"
    $imageSaved = Save-DockerImage -imageName $imageName -outputPath $imageFile
    
    if (-not $imageSaved) {
        return $false
    }
    
    # Copy sync scripts
    $scriptFiles = @(
        "sync_docker_env.bat",
        "enable_docker_remote.ps1",
        "sync_base_server_image.ps1",
        "desktop_sync_base_server.ps1",
        "docker_sync_quickstart.ps1"
    )
    
    $docsFiles = @(
        "Docker Sync Setup Guide.md",
        "Base_Server_01_Sync_Summary.md"
    )
    
    Write-Host "Copying sync scripts and documentation..." -ForegroundColor Yellow
    
    foreach ($file in $scriptFiles) {
        if (Test-Path $file) {
            $destination = Join-Path $outputDir $file
            Copy-Item -Path $file -Destination $destination -Force
            Write-Host "Copied: $file" -ForegroundColor Green
        }
        else {
            Write-Host "Warning: File '$file' not found. Skipping." -ForegroundColor Yellow
        }
    }
    
    foreach ($file in $docsFiles) {
        if (Test-Path $file) {
            $destination = Join-Path $outputDir $file
            Copy-Item -Path $file -Destination $destination -Force
            Write-Host "Copied: $file" -ForegroundColor Green
        }
        else {
            Write-Host "Warning: File '$file' not found. Skipping." -ForegroundColor Yellow
        }
    }
    
    # Create README file
    $readmePath = Join-Path $outputDir "README.txt"
    
    $readmeContent = @"
| Docker Sync Package
| ===================
| 
| This package contains everything needed to synchronize the $imageName Docker environment.
| 
| Contents:
| - $imageName-image.tar: Docker image file
| - sync_docker_env.bat: Batch script for Docker synchronization
| - enable_docker_remote.ps1: PowerShell script to enable Docker remote access
| - sync_base_server_image.ps1: PowerShell script for image synchronization
| - desktop_sync_base_server.ps1: PowerShell script for desktop synchronization
| - docker_sync_quickstart.ps1: Quick start PowerShell script
| - Docker Sync Setup Guide.md: Detailed documentation
| - Base_Server_01_Sync_Summary.md: Summary documentation
| 
| Quick Start:
| 1. Ensure Docker Desktop is installed and running
| 2. Run sync_docker_env.bat
| 3. Choose option 1 (Quick Start)
| 4. Follow the prompts to load the image and create a container
| 
| For detailed instructions, see the Docker Sync Setup Guide.md file.
| "@
    
    Set-Content -Path $readmePath -Value $readmeContent
    Write-Host "Created: README.txt" -ForegroundColor Green
    
    # Create ZIP archive
    $zipPath = "${outputDir}.zip"
    
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    
    try {
        Write-Host "Creating ZIP archive..." -ForegroundColor Yellow
        Compress-Archive -Path $outputDir -DestinationPath $zipPath
        Write-Host "Created ZIP archive: $zipPath" -ForegroundColor Green
    }
    catch {
        Write-Host "Error creating ZIP archive: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Display success message
    Show-Header "Sync Package Created"
    
    Write-Host "Docker sync package has been created successfully." -ForegroundColor Green
    Write-Host
    Write-Host "Package directory: $outputDir" -ForegroundColor Yellow
    Write-Host "ZIP archive: $zipPath" -ForegroundColor Yellow
    Write-Host
    Write-Host "To use this package on another machine:" -ForegroundColor Yellow
    Write-Host "1. Copy the package directory or ZIP archive to the target machine" -ForegroundColor Yellow
    Write-Host "2. Extract the ZIP archive if necessary" -ForegroundColor Yellow
    Write-Host "3. Run sync_docker_env.bat or docker_sync_quickstart.ps1" -ForegroundColor Yellow
    Write-Host "4. Follow the prompts to load the image and create a container" -ForegroundColor Yellow
    
    return $true
}

# Run the main function
Create-SyncPackage