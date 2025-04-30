#!/bin/bash

echo "🚀 Setting up sales-and-inventory-management"

echo "🔨 Building Docker image..."
docker build -t sales-and-inventory-management:1.0 .


if [ $? -ne 0 ]; then
  echo "❌ Error: Docker image build failed!"
  exit 1
fi

echo "🚀 Starting Docker containers in detached mode..."
docker run -d -p 8000:8000 sales-and-inventory-management:1.0

if [ $? -ne 0 ]; then
  echo "❌ Error: Docker container failed to start!"
  exit 1
fi

echo "✔️ Setup completed successfully!"