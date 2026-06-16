# Stage 1: Build the application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files from the submodule
COPY stt-arena-design/package*.json ./

# Install dependencies including peer dependencies
RUN npm install --legacy-peer-deps

# Install react-is explicitly to avoid resolution issues
RUN npm install --legacy-peer-deps react-is

# Copy the rest of the submodule application code
COPY stt-arena-design/ ./

# Bundle the real audio sample so the arena can transcribe genuine audio
RUN mkdir -p ./public
COPY samples/proklamasi.mp3 ./public/proklamasi.mp3

# Apply build-time patches (real-audio battles, availability flags, size variants)
COPY patch_app.cjs ./
RUN node patch_app.cjs

# Build the application (Vite frontend + esbuild server)
ENV NODE_ENV=production
RUN npm run build

# Stage 2: Run the application
FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app/package*.json ./
RUN npm install --omit=dev --legacy-peer-deps && npm install --legacy-peer-deps vite

# Copy built artifacts (dist containing index.html, static assets, and server.cjs)
COPY --from=builder /app/dist ./dist
COPY bootstrap.js ./bootstrap.js

# Expose port 3000 (default for stt-arena-design Express server)
EXPOSE 3000

ENV NODE_ENV=production

# Start the compiled Express server through the bootstrap wrapper
CMD ["node", "bootstrap.js"]
