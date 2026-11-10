#!/usr/bin/env bash
# CrewPass — atualização: pull + rebuild (migrate roda no entrypoint).
set -euo pipefail
git pull
docker compose up -d --build
docker compose ps
echo "Pronto. Logs: docker compose logs -f web"