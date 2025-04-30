FROM node:16-alpine

# Create app directory
WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Start with a command that explicitly logs to stdout
CMD ["node", "index.js"]