FROM python:3.11-slim

# Install dependencies for nsjail
RUN apt-get update && apt-get install -y \
    autoconf \
    bison \
    flex \
    gcc \
    g++ \
    git \
    libnl-route-3-dev \
    libtool \
    make \
    pkg-config \
    protobuf-compiler \
    libprotobuf-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone and build nsjail
RUN git clone https://github.com/google/nsjail.git /nsjail && \
    cd /nsjail && \
    make && \
    mv /nsjail/nsjail /usr/local/bin/ && \
    rm -rf /nsjail

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install commonly used libraries for user scripts
RUN pip install --no-cache-dir pandas numpy

# Copy application files
COPY app.py .
COPY nsjail.cfg .

# Create necessary directories
RUN mkdir -p /tmp/nsjail

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]