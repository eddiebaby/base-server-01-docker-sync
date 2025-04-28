FROM node:16-alpine

# Create app directory
WORKDIR /app

# Install git for updates
RUN apk add --no-cache git

# Install pm2 globally for process management
RUN npm install -g pm2

# Copy package files first (better caching)
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Create data directory if it doesn't exist
RUN mkdir -p /app/data

# Set up scheduled updates (runs every 6 hours)
RUN echo "0 */6 * * * cd /app && node scripts/update-script.js >> /app/data/update.log 2>&1" > /etc/crontabs/root
RUN crond

# Expose the application port
EXPOSE 8080

# Start the application
CMD ["pm2-runtime", "start", "index.js", "--name", "mcp-server"]