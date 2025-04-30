Set-Content -Path "$PSScriptRoot/Dockerfile" -Value @"
FROM mcr.microsoft.com/dotnet/sdk:7.0 AS build
WORKDIR /app

# Copy csproj and restore dependencies
COPY *.csproj ./
RUN dotnet restore

# Copy only necessary files for build (exclude bin, obj, etc.)
COPY ./Program.cs ./
COPY ./Properties/ ./Properties/
COPY ./Controllers/ ./Controllers/
COPY ./Models/ ./Models/
COPY ./Services/ ./Services/
COPY ./appsettings*.json ./
# If you have additional project files, add them here

# Build the application
RUN dotnet publish -c Release -o out || exit 1

# Use multi-stage build for smaller final image
FROM mcr.microsoft.com/dotnet/aspnet:7.0 AS runtime
WORKDIR /app

# Copy only the published output from build stage
COPY --from=build /app/out ./

# Set proper environment variables
ENV ASPNETCORE_URLS=http://+:80
ENV DOTNET_RUNNING_IN_CONTAINER=true

# Add healthcheck for better operational reliability
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:80/health || exit 1

# Set proper entry point with explicit command
ENTRYPOINT ["dotnet", "TestApp.dll"]
"@