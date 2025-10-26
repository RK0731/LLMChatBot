#!/usr/bin/env bash
# Author: Liu Renke
docker build -t renkebot-app:latest \
    -f deployment/dockerfile-app --platform linux/amd64 .

docker image prune -f