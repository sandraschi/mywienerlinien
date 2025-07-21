# Use Node.js Alpine for smaller image size
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install docsify-cli globally
RUN npm install -g docsify-cli

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies if they exist
RUN if [ -f package.json ]; then npm install; fi

# Copy all documentation files
COPY . .

# Expose port 3300
EXPOSE 3300

# Create a health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3300/ || exit 1

# Use a startup script for better process management
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["docsify", "serve", ".", "--port", "3300"] 