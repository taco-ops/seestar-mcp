# SeestarS50 MCP Server Docker Image

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install dependencies with uv
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash seestar && \
    chown -R seestar:seestar /app
USER seestar

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/src
ENV SEESTAR_HOST=""
ENV SEESTAR_PORT=4700
ENV LOG_LEVEL=DEBUG

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD uv run python -c "import seestar_mcp; print('OK')" || exit 1

# Default command - keep container running for MCP connections
# MCP clients will connect via: docker exec -i seestar-mcp-server uv run seestar-mcp
CMD ["sh", "-c", "while true; do sleep 3600; done"]
