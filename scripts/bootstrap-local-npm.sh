#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NPM_VERSION="${NPM_VERSION:-11.6.4}"

cd "${ROOT_DIR}"
mkdir -p .local/npm .local/npm-cache

if [[ -f .local/npm/bin/npm-cli.js ]]; then
  node .local/npm/bin/npm-cli.js --version
  exit 0
fi

curl -L "https://registry.npmjs.org/npm/-/npm-${NPM_VERSION}.tgz" -o .local/npm.tgz
tar -xzf .local/npm.tgz -C .local/npm --strip-components=1
node .local/npm/bin/npm-cli.js --version

