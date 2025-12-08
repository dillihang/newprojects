# ------------ Stage 1: Builder --------------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies for any compiled packages
RUN apt-get update && apt-get install -y build-essential

# Copy only dependency file first (for caching)
COPY requirements.txt .

# Install dependencies into a separate folder
RUN pip install --prefix=/install -r requirements.txt


# ------------ Stage 2: Final Image --------------
FROM python:3.11-slim

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app.py .

# Expose port for the web server
EXPOSE 5000

# Run the server
CMD ["python", "app.py"]
