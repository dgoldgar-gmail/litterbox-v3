#!/bin/bash

# --- Configuration ---
REGISTRY_HOST="192.168.50.15:5000"
IMAGE_NAME="litterbox-v3"
TAG="0.2"
GENERIC_IMAGE="${REGISTRY_HOST}/${IMAGE_NAME}:${TAG}"
BUILDER_NAME="multiarch-builder"

echo "--- 1. Registering Architecture Emulators ---"
docker run --privileged --rm tonistiigi/binfmt --install all

echo "--- 2. Ensuring Builder Exists ---"
# Check if the builder exists. If not, create it.
if ! docker buildx inspect "$BUILDER_NAME" > /dev/null 2>&1; then
    echo "Builder not found. Creating $BUILDER_NAME..."
    
    # Create the config file only during creation
    cat <<EOF > buildkitd.toml
[registry."${REGISTRY_HOST}"]
  http = true
  insecure = true
EOF

    docker buildx create --name "$BUILDER_NAME" \
      --config buildkitd.toml \
      --driver docker-container --use
    rm buildkitd.toml
else
    echo "Reusing existing builder: $BUILDER_NAME"
    docker buildx use "$BUILDER_NAME"
fi

# Ensure the builder is running
docker buildx inspect --bootstrap

echo "--- 3. Starting Build & Push ---"
# Note: Subsequent runs will be much faster because layers are cached inside the builder container
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag "${GENERIC_IMAGE}" \
    --push \
    --progress auto \
    .

if [ $? -eq 0 ]; then
    echo "SUCCESS: ${GENERIC_IMAGE} pushed."
else
    echo "ERROR: Build failed."
    exit 1
fi
