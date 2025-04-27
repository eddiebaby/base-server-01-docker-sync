@echo off
setlocal enabledelayedexpansion

:: Docker Environment Synchronization Script
:: This script helps synchronize Docker environments between machines

:: Set colors for console output
set "CYAN=[36m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "RESET=[0m"

:: Function to display a header
:show_header
echo.
echo %CYAN%===== %~1 =====%RESET%
echo.
goto :eof

:: Function to check if Docker is running
:check_docker
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo %RED%Error: Docker is not running or not installed.%RESET%
    echo %RED%Please start Docker Desktop and try again.%RESET%
    exit /b 1
)
goto :eof

:: Main menu
:main_menu
cls
call :show_header "Docker Environment Synchronization"

call :check_docker
if %ERRORLEVEL% neq 0 exit /b 1

echo %YELLOW%1. Quick Start%RESET%
echo %YELLOW%2. Save Docker Image%RESET%
echo %YELLOW%3. Load Docker Image%RESET%
echo %YELLOW%4. Enable Docker Remote Access%RESET%
echo %YELLOW%5. Test Docker Synchronization%RESET%
echo %YELLOW%6. Exit%RESET%
echo.

set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto quick_start
if "%choice%"=="2" goto save_image
if "%choice%"=="3" goto load_image
if "%choice%"=="4" goto enable_remote
if "%choice%"=="5" goto test_sync
if "%choice%"=="6" goto end
echo %RED%Invalid choice. Please try again.%RESET%
pause
goto main_menu

:: Quick Start
:quick_start
cls
call :show_header "Quick Start"

echo %YELLOW%1. Save Docker image (on source machine)%RESET%
echo %YELLOW%2. Load Docker image (on target machine)%RESET%
echo %YELLOW%3. Create and start container (on target machine)%RESET%
echo %YELLOW%4. Test synchronization%RESET%
echo %YELLOW%5. Back to main menu%RESET%
echo.

set /p quick_choice="Enter your choice (1-5): "

if "%quick_choice%"=="1" goto quick_save
if "%quick_choice%"=="2" goto quick_load
if "%quick_choice%"=="3" goto quick_create
if "%quick_choice%"=="4" goto test_sync
if "%quick_choice%"=="5" goto main_menu
echo %RED%Invalid choice. Please try again.%RESET%
pause
goto quick_start

:: Quick Save
:quick_save
cls
call :show_header "Save Docker Image"

set image_name=base_server_01
set /p image_name="Enter the image name (default: base_server_01): "

set output_path=base_server_01-image.tar
set /p output_path="Enter the path to save the image file (default: base_server_01-image.tar): "

echo %YELLOW%Saving image '%image_name%' to '%output_path%'...%RESET%
echo %YELLOW%This may take several minutes. Please wait...%RESET%

docker save -o "%output_path%" %image_name%

if %ERRORLEVEL% equ 0 (
    echo %GREEN%Image saved successfully.%RESET%
) else (
    echo %RED%Failed to save image. Exit code: %ERRORLEVEL%%RESET%
)

pause
goto main_menu

:: Quick Load
:quick_load
cls
call :show_header "Load Docker Image"

set input_path=base_server_01-image.tar
set /p input_path="Enter the path to the image file (default: base_server_01-image.tar): "

if not exist "%input_path%" (
    echo %RED%Error: File '%input_path%' does not exist.%RESET%
    pause
    goto quick_start
)

echo %YELLOW%Loading image from '%input_path%'...%RESET%
echo %YELLOW%This may take several minutes. Please wait...%RESET%

docker load -i "%input_path%"

if %ERRORLEVEL% equ 0 (
    echo %GREEN%Image loaded successfully.%RESET%
) else (
    echo %RED%Failed to load image. Exit code: %ERRORLEVEL%%RESET%
)

pause
goto main_menu

:: Quick Create
:quick_create
cls
call :show_header "Create and Start Container"

set image_name=base_server_01
set /p image_name="Enter the image name (default: base_server_01): "

set container_name=base_server_01_instance
set /p container_name="Enter the container name (default: base_server_01_instance): "

set host_port=5001
set /p host_port="Enter the host port (default: 5001): "

set container_port=5000
set /p container_port="Enter the container port (default: 5000): "

:: Check if container already exists
docker ps -a --filter "name=%container_name%" -q > temp.txt
set /p container_exists=<temp.txt
del temp.txt

if not "%container_exists%"=="" (
    echo %YELLOW%Container '%container_name%' already exists.%RESET%
    set /p remove_container="Do you want to remove it and create a new one? (y/n): "
    
    if /i "%remove_container%"=="y" (
        echo %YELLOW%Removing container '%container_name%'...%RESET%
        docker rm -f %container_name% >nul 2>&1
        
        if %ERRORLEVEL% neq 0 (
            echo %RED%Failed to remove container. Exit code: %ERRORLEVEL%%RESET%
            pause
            goto main_menu
        )
    ) else (
        echo %YELLOW%Container creation aborted.%RESET%
        pause
        goto main_menu
    )
)

echo %YELLOW%Creating container '%container_name%' from image '%image_name%'...%RESET%
docker create -p %host_port%:%container_port% --name %container_name% %image_name%

if %ERRORLEVEL% equ 0 (
    echo %GREEN%Container created successfully.%RESET%
    
    set /p start_container="Do you want to start the container? (y/n): "
    
    if /i "%start_container%"=="y" (
        echo %YELLOW%Starting container '%container_name%'...%RESET%
        docker start %container_name%
        
        if %ERRORLEVEL% equ 0 (
            echo %GREEN%Container started successfully.%RESET%
        ) else (
            echo %RED%Failed to start container. Exit code: %ERRORLEVEL%%RESET%
        )
    )
) else (
    echo %RED%Failed to create container. Exit code: %ERRORLEVEL%%RESET%
)

pause
goto main_menu

:: Save Docker Image
:save_image
cls
call :show_header "Save Docker Image"

:: List available images
echo %YELLOW%Available Docker images:%RESET%
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.Size}}"
echo.

set /p image_name="Enter the image name to save: "
set /p output_path="Enter the path to save the image file: "

echo %YELLOW%Saving image '%image_name%' to '%output_path%'...%RESET%
echo %YELLOW%This may take several minutes. Please wait...%RESET%

docker save -o "%output_path%" %image_name%

if %ERRORLEVEL% equ 0 (
    echo %GREEN%Image saved successfully.%RESET%
) else (
    echo %RED%Failed to save image. Exit code: %ERRORLEVEL%%RESET%
)

pause
goto main_menu

:: Load Docker Image
:load_image
cls
call :show_header "Load Docker Image"

set /p input_path="Enter the path to the image file: "

if not exist "%input_path%" (
    echo %RED%Error: File '%input_path%' does not exist.%RESET%
    pause
    goto main_menu
)

echo %YELLOW%Loading image from '%input_path%'...%RESET%
echo %YELLOW%This may take several minutes. Please wait...%RESET%

docker load -i "%input_path%"

if %ERRORLEVEL% equ 0 (
    echo %GREEN%Image loaded successfully.%RESET%
    
    set /p create_container="Do you want to create a container from this image? (y/n): "
    
    if /i "%create_container%"=="y" (
        set /p image_name="Enter the image name: "
        set /p container_name="Enter a name for the container: "
        set /p host_port="Enter the host port (default: 5001): "
        
        if "%host_port%"=="" set host_port=5001
        
        set /p container_port="Enter the container port (default: 5000): "
        
        if "%container_port%"=="" set container_port=5000
        
        echo %YELLOW%Creating container '%container_name%' from image '%image_name%'...%RESET%
        docker create -p %host_port%:%container_port% --name %container_name% %image_name%
        
        if %ERRORLEVEL% equ 0 (
            echo %GREEN%Container created successfully.%RESET%
            
            set /p start_container="Do you want to start the container? (y/n): "
            
            if /i "%start_container%"=="y" (
                echo %YELLOW%Starting container '%container_name%'...%RESET%
                docker start %container_name%
                
                if %ERRORLEVEL% equ 0 (
                    echo %GREEN%Container started successfully.%RESET%
                ) else (
                    echo %RED%Failed to start container. Exit code: %ERRORLEVEL%%RESET%
                )
            )
        ) else (
            echo %RED%Failed to create container. Exit code: %ERRORLEVEL%%RESET%
        )
    )
) else (
    echo %RED%Failed to load image. Exit code: %ERRORLEVEL%%RESET%
)

pause
goto main_menu

:: Enable Docker Remote Access
:enable_remote
cls
call :show_header "Enable Docker Remote Access"

echo %YELLOW%This will run the PowerShell script to enable Docker remote access.%RESET%
echo %YELLOW%Administrator privileges are required.%RESET%
echo.
set /p confirm="Do you want to continue? (y/n): "

if /i not "%confirm%"=="y" goto main_menu

powershell -ExecutionPolicy Bypass -File "enable_docker_remote.ps1"

pause
goto main_menu

:: Test Docker Synchronization
:test_sync
cls
call :show_header "Test Docker Synchronization"

set container_name=base_server_01_instance
set /p container_name="Enter the container name to test (default: base_server_01_instance): "

:: Check if Docker is running
echo %YELLOW%Checking if Docker is running...%RESET%
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo %RED%Error: Docker is not running or not installed.%RESET%
    pause
    goto main_menu
)
echo %GREEN%Docker is running.%RESET%

:: Check if container exists
echo %YELLOW%Checking if container '%container_name%' exists...%RESET%
docker ps -a --filter "name=%container_name%" -q > temp.txt
set /p container_exists=<temp.txt
del temp.txt

if "%container_exists%"=="" (
    echo %RED%Error: Container '%container_name%' does not exist.%RESET%
    pause
    goto main_menu
)
echo %GREEN%Container exists.%RESET%

:: Check if container is running
echo %YELLOW%Checking if container is running...%RESET%
docker ps --filter "name=%container_name%" -q > temp.txt
set /p container_running=<temp.txt
del temp.txt

if "%container_running%"=="" (
    echo %YELLOW%Container is not running.%RESET%
    set /p start_container="Do you want to start it? (y/n): "
    
    if /i "%start_container%"=="y" (
        echo %YELLOW%Starting container '%container_name%'...%RESET%
        docker start %container_name%
        
        if %ERRORLEVEL% equ 0 (
            echo %GREEN%Container started successfully.%RESET%
        ) else (
            echo %RED%Failed to start container. Exit code: %ERRORLEVEL%%RESET%
            pause
            goto main_menu
        )
    ) else {
        pause
        goto main_menu
    }
) else (
    echo %GREEN%Container is running.%RESET%
)

:: Check container health
echo %YELLOW%Checking container health...%RESET%
docker inspect --format="{{.State.Status}}" %container_name% > temp.txt
set /p container_status=<temp.txt
del temp.txt

echo %GREEN%Container status: %container_status%%RESET%

:: Check port mappings
echo %YELLOW%Checking port mappings...%RESET%
docker port %container_name%
echo.

:: Execute a test command in the container
echo %YELLOW%Executing test command in container...%RESET%
docker exec %container_name% echo "Container is working properly"

echo.
echo %GREEN%Test completed.%RESET%

pause
goto main_menu

:end
echo %YELLOW%Exiting...%RESET%
endlocal
exit /b 0