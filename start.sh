#!/bin/bash
set -e
IMAGE_NAME="obscur"
docker run \
  --name obscur \
  --env-file .env \
  -v "./rss:/home/tor-scraper/rss" \
  -v "./config:/home/tor-scraper/config" \
  -v "./data:/home/tor-scraper/data" \
  -v "./nltk_data:/home/tor-scraper/nltk_data" \
  --network container:obscur-tor \
  --rm \
  "$IMAGE_NAME"