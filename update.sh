#!/bin/bash
git pull
docker compose build s_media_service
docker compose up -d
