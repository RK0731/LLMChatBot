#!/usr/bin/env bash
# Author: Liu Renke

# Base image for linux/amd64 env

docker build -t renkebot-base-image:latest -f deployment/dockerfile-base-image --platform linux/amd64 .
docker image prune -f