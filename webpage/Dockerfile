# Build stage
FROM node:20-alpine AS builder

# Install pnpm
RUN corepack enable && corepack prepare pnpm@10.4.1 --activate

# Set working directory
WORKDIR /app

# Copy package files first (for better layer caching)
COPY YPCA-main/package.json YPCA-main/pnpm-lock.yaml* ./

# Install dependencies
# Use --no-frozen-lockfile to allow lockfile refresh inside container when package.json changed
RUN pnpm install --no-frozen-lockfile

# Copy the rest of the application source (including .env file)
COPY YPCA-main/ ./

# Build the application
# Vite will automatically read .env file from the project root
RUN pnpm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config (optional, for SPA routing)
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # Gzip compression \
    gzip on; \
    gzip_vary on; \
    gzip_min_length 1024; \
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript; \
    \
    # SPA routing - serve index.html for all routes \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    # Cache static assets \
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Copy built files from builder stage
COPY --from=builder /app/dist/public /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

