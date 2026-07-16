# Dockerfile for MySQL FastMCP Agent

FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY agent.py .
COPY mysql_connector.py .
COPY mcp_tools.py .
COPY server.py .
COPY tool_registry.py .

# Command to run the FastMCP server over SSE
CMD ["python", "server.py", "--transport", "sse", "--port", "8005"]
