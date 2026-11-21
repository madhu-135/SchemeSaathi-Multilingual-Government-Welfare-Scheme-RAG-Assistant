# Multi-stage Dockerfile for SchemeSaathi React Frontend
# Stage 1: Build production bundle using Node 20
FROM node:20-alpine AS build

WORKDIR /app

# Cache dependencies
COPY package*.json ./
RUN npm ci || npm install

# Copy source files and build
COPY . .
RUN npm run build

# Stage 2: Serve with lightweight Nginx alpine image
FROM nginx:alpine

# Remove default static pages
RUN rm -rf /usr/share/nginx/html/*

# Copy Vite build output
COPY --from=build /app/dist /usr/share/nginx/html

# Copy reverse proxy Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

