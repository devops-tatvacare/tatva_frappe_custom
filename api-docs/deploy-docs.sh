#!/usr/bin/env bash
# Build the Zudoku API docs and deploy them to https://one.tatvacare.in/docs
#
# Content-only: builds this project and ships the static output into the Frappe
# sites volume. Does NOT touch nginx/compose — the /docs route is permanent
# (nginx/frappe.conf.template, bind-mounted via crm-compose.yml; runbook Phase 17).
#
# Update docs = edit pages/*.mdx or openapi.json -> run this script. Seconds, no restart.
# Requires: node, npm, expect.   Run:  ./deploy-docs.sh   (from this api-docs/ dir)
set -euo pipefail

# VM connection details come from the environment — NEVER hardcode them (this repo is public).
#   export VM_SSH_HOST='<vm-ip-or-host>'  VM_SSH_PW='<password>'  [VM_SSH_USER=frappe]
VM="${VM_SSH_HOST:?Set VM_SSH_HOST (the VM IP/host)}" ; SSHUSER="${VM_SSH_USER:-frappe}" ; PW="${VM_SSH_PW:?Set VM_SSH_PW (the VM SSH password)}"
DEST=/home/frappe/frappe-bench/sites/crm.local/public
PROJ="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJ"

echo "[1/4] build"
[ -d node_modules ] || npm install
npm run build

# Strip Zudoku's CDN preconnect hint from the built HTML (no asset loads from it;
# this just removes the last 'zudoku' reference from the served markup). Durable —
# runs on every build so it can't regress.
find dist/docs -name '*.html' -print0 | xargs -0 perl -i -pe 's{<link[^>]*cdn\.zudoku\.dev[^>]*>}{}g'

echo "[2/4] package dist/docs"
tar czf /tmp/zudoku-dist.tgz -C dist/docs .

echo "[3/4] upload tarball"
expect <<EXP
set timeout 240
spawn scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR /tmp/zudoku-dist.tgz $SSHUSER@$VM:/tmp/zudoku-dist.tgz
expect "password:"; send "$PW\r"; expect eof
EXP

echo "[4/4] deploy into Frappe sites volume (atomic swap)"
expect <<EXP
set timeout 240
spawn ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR $SSHUSER@$VM "rm -rf /tmp/zdocs && mkdir -p /tmp/zdocs && tar xzf /tmp/zudoku-dist.tgz -C /tmp/zdocs && docker compose -p crm exec -T backend rm -rf $DEST/docs $DEST/docs_staging && docker compose -p crm cp /tmp/zdocs backend:$DEST/docs_staging && docker compose -p crm exec -T backend sh -c 'mv $DEST/docs_staging $DEST/docs && chown -R frappe:frappe $DEST/docs' && echo DOCS_DEPLOYED"
expect "password:"; send "$PW\r"; expect eof
EXP

echo "Done -> verify https://one.tatvacare.in/docs"
