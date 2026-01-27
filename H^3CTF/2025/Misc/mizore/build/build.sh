#! /bin/bash
docker compose up --build --force-recreate -d \
|| (echo "[-] Something went wrong. You may haven't fill \`container_name\` and \`image\` in docker-compose.yml." && exit 1)