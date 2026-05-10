#!/usr/bin/env bash
set -euo pipefail

: "${SONAR_TOKEN:?Set SONAR_TOKEN first}"

PROJECT_KEY="tokintmash_icloud-downloader"
OUT_FILE="sonar-issues.json"

curl --fail --silent --show-error \
  -H "Authorization: Bearer $SONAR_TOKEN" \
  "https://sonarcloud.io/api/issues/search?componentKeys=${PROJECT_KEY}&resolved=false&ps=500&p=1" \
  -o "$OUT_FILE"


curl -H "Authorization: Bearer $SONAR_TOKEN" \
  "https://sonarcloud.io/api/issues/search?componentKeys=tokintmash_icloud-downloader&resolved=false&ps=500&p=1" \
  -o sonar-issues.json

curl.exe --fail --silent --show-error `
  -H "Authorization: Bearer $env:SONAR_TOKEN" `
  --get "https://sonarcloud.io/api/issues/search" `
  --data-urlencode "componentKeys=tokintmash_icloud-downloader" `
  --data-urlencode "resolved=false" `
  --data-urlencode "ps=500" `
  --data-urlencode "p=1" `
  -o sonar-issues.json