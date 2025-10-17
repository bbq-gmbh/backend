FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev --compile-bytecode --no-python-downloads

# Copy application code
COPY app ./app

# Expose the port
EXPOSE 3001

# Run the application
CMD ["uv", "run", "fastapi", "run", "--host", "0.0.0.0", "--port", "3001", "app/main.py"]