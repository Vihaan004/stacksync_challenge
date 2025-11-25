# Stage 1: Build nsjail
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    autoconf bison flex gcc g++ git libprotobuf-dev libnl-route-3-dev \
    libtool make pkg-config protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Build nsjail
RUN git clone --depth 1 https://github.com/google/nsjail.git /nsjail_src && \
    cd /nsjail_src && \
    make && \
    strip /nsjail_src/nsjail

# Stage 2: Runtime image
FROM python:3.11-slim

# Install only runtime dependencies for nsjail (no build tools!)
RUN apt-get update && apt-get install -y \
    libprotobuf32 libnl-route-3-200 \
    && rm -rf /var/lib/apt/lists/*

# Copy only the nsjail binary from builder stage
COPY --from=builder /nsjail_src/nsjail /usr/local/bin/nsjail

# Setup application
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Setup nsjail temp directory
RUN mkdir -p /tmp/nsjail && chmod 777 /tmp/nsjail

# Copy application files
COPY app.py .
COPY nsjail.cfg .

# Expose port and run
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "30", "app:app"]