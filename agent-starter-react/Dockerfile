# Multi-stage Dockerfile for Next.js React Application
# Optimized for both development and production builds

# Base image with Node.js and pnpm
FROM node:20-alpine AS base

# Install pnpm globally
RUN npm install -g pnpm

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Development stage
FROM base AS development

# Copy all source files
COPY . .

# Expose development port
EXPOSE 3000

# Set environment to development
ENV NODE_ENV=development

# Start development server with turbopack
CMD ["pnpm", "dev"]

# Build stage for production
FROM base AS builder

# Copy all source files
COPY . .

# Build the application
RUN pnpm build

# Production stage
FROM node:20-alpine AS production

# Install pnpm
RUN npm install -g pnpm

WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install only production dependencies
RUN pnpm install --prod --frozen-lockfile

# Copy built application from builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/app-config.ts ./

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Change ownership of the app directory
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose production port
EXPOSE 3000

# Set environment to production
ENV NODE_ENV=production

# Start production server
CMD ["pnpm", "start"]