#!/bin/bash

# Variables (customize these as needed)
JUPYTER_IMAGE="jupyter/base-notebook"  # Docker image for Jupyter Notebook
#NOTEBOOK_DIR="/home/llama/jupyter-server" 
NOTEBOOK_DIR="/home/llama/llamastack-lab"
HOST_PORT=9443                         # Port to access Jupyter Notebook on the host
CONTAINER_PORT=8888                    # Port inside the container

# Ensure the notebook directory exists
mkdir -p "$NOTEBOOK_DIR"

sudo chcon -Rt svirt_sandbox_file_t "$NOTEBOOK_DIR"
chmod -R 777 "$NOTEBOOK_DIR"

# Run the Jupyter container
echo "Starting Jupyter Notebook container..."
podman pull "$JUPYTER_IMAGE"

# podman run -d --name jupyter-notebook --net=host \
#   -v "$NOTEBOOK_DIR:/home/jovyan/work:z" \
#   "$JUPYTER_IMAGE"

# podman run -d --name jupyter-notebook1 \
#   -p "$HOST_PORT:$CONTAINER_PORT" \
#   -v "$NOTEBOOK_DIR:/home/jovyan/work:z" \
#   "$JUPYTER_IMAGE"

# podman run -d --name jupyter-notebook1 \
#   -p "$HOST_PORT:$CONTAINER_PORT" \
#   -v "$NOTEBOOK_DIR:/home/jovyan/work:z" \
#   "$JUPYTER_IMAGE" start-notebook.sh \
#   --NotebookApp.token='' \
#   --NotebookApp.password=''  


podman run -d --name jupyter-notebook1 \
  --network=host \
  -v "$NOTEBOOK_DIR:/home/jovyan/work:z" \
  "$JUPYTER_IMAGE" start-notebook.sh \
  --NotebookApp.token='' \
  --NotebookApp.password='' \
  --port=9443

echo "Jupyter Notebook is running."
echo "Access it at http://localhost:$HOST_PORT"
echo "Your notebooks are stored in: $NOTEBOOK_DIR"

# Instructions for stopping the container
echo "To stop the container, run: docker stop jupyter-notebook"

