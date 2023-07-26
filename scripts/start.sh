#!/bin/bash
# Start FLLC CyberDeck
cd "$(dirname "$0")/../infra/docker"
docker compose up --build
