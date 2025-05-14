# MCP Parks Info Server

This document explains how to prepare your environment, run the MCP server directly with Uvicorn, and build & run it in a container using Docker or Podman.

## 1. Preparing the environment

```bash
# Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies from pyproject.toml
pip install --upgrade pip
pip install .
```

## 2. Running the MCP server directly

From the `mcp-parks-info` folder, run:

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8007
```

Your server will be available at `http://localhost:8007/mcp`.

## 3. Building and running the container

Both Docker and Podman use the same `Containerfile` in this directory.

### Podman

```bash
# Build the image
podman build -t mcp-parks-info:latest -f Containerfile .

# Run the container on port 9000
podman run -d \

  -e PORT=9000 \
  --network=host\
  

podman run -d --name mcp-parks-info --network=host \
  -e GOOGLE_MAPS_API_KEY="ENTER_YOUR_TOKEN" \
  -e MCP_PORT=8006 mcp-parks-info:latest

```
# If running to debug, you can quickly run: 
podman run -e PORT=9000 --network=host -p 9000:9000 mcp-parks-info:latest

### Docker

```bash
# Build the image
docker build -t mcp-parks-info:latest -f Containerfile .

# Run the container on port 9000
docker run -d \
  -e PORT=9000 \
  -p 9000:9000 \
  mcp-parks-info:latest