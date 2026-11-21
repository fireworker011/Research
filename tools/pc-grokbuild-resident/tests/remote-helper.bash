#!/usr/bin/env bash
# Exercise the Linux helper against a local pwsh queue. No PC required.
set -euo pipefail

TOOL=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
HELPER="$TOOL/linux/grokbuild-remote.sh"
ROOT=$(mktemp -d)
export GROKBUILD_LOCAL=1
export GROKBUILD_ROOT="$ROOT"

fail() { echo "FAIL $*" >&2; exit 1; }

show_status=$("$HELPER" show status job1)
echo "$show_status" | grep -q "Join-Path" || fail "status script missing Join-Path"
echo "$show_status" | grep -q "Documents" || fail "status script missing default root"
echo "$show_status" | grep -q "\.json" || fail "status script missing json"

"$HELPER" show push "$TOOL/examples/readonly-order.md" | grep -q "inbox" || fail "push script missing inbox"

set +e
"$HELPER" status '../bad'
bad_code=$?
set -e
[[ "$bad_code" -eq 2 ]] || fail "bad id exit $bad_code"

push_out=$("$HELPER" push "$TOOL/examples/readonly-order.md")
echo "$push_out" | grep -q '^id=example-readonly' || fail "push id: $push_out"
remote_file=$(printf '%s\n' "$push_out" | sed -n 's/^file=//p')
inbox_file="$ROOT/queue/inbox/$remote_file"
[[ -f "$inbox_file" ]] || fail "inbox file missing"
grep -q '^sha256: ' "$inbox_file" || fail "sha not stamped"
python3 - "$inbox_file" <<'PY'
import hashlib, pathlib, re, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
m = re.match(r"\A---\n(.*?)\n---(?:\n(.*))?\Z", text, re.S)
front, body = m.group(1), m.group(2) or ""
digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
found = re.search(r"(?m)^sha256:\s*([0-9a-f]+)\s*$", front)
if not found or found.group(1) != digest:
    raise SystemExit("stamped sha does not match body")
PY

status_json=$("$HELPER" status example-readonly)
python3 -c 'import json,sys; assert json.loads(sys.stdin.read())["state"]=="missing"' <<<"$status_json"

"$HELPER" deny example-readonly >/dev/null
[[ -f "$ROOT/queue/confirm/example-readonly.ng" ]] || fail "ng missing"

set +e
"$HELPER" approve example-readonly
approve_blocked=$?
set -e
[[ "$approve_blocked" -eq 3 ]] || fail "approve without json exit $approve_blocked"

mkdir -p "$ROOT/queue/confirm" "$ROOT/queue/status" "$ROOT/queue/done" "$ROOT/queue/logs"
printf '%s\n' '{"job_id":"other1"}' > "$ROOT/queue/confirm/other1.json"
"$HELPER" approve other1 >/dev/null
[[ -f "$ROOT/queue/confirm/other1.ok" ]] || fail "ok missing"

python3 - "$ROOT" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = {
    "id": "other1",
    "state": "done",
    "lane": "readonly",
    "reasoning": "xhigh",
    "model": "grok-4.7",
    "start": "2026-11-21T00:00:00Z",
    "end": "2026-11-21T00:01:00Z",
    "exit_code": 0,
    "pid": 1,
    "order_file": "other1.md",
    "error": None,
    "confirm_decision": None,
    "confirm_since": None,
    "host": "LAPTOP-PL4TICBO",
    "user": "hp",
}
(root / "queue" / "status" / "other1.json").write_text(json.dumps(status), encoding="utf-8")
(root / "queue" / "done" / "other1.md").write_text("hello\n", encoding="utf-8")
(root / "queue" / "logs" / "other1.log").write_text("password=hunter2\n", encoding="utf-8")
PY

"$HELPER" pull other1 "$ROOT/pulled" >/dev/null
[[ -f "$ROOT/pulled/status.json" ]] || fail "pull status"
[[ -f "$ROOT/pulled/order.md" ]] || fail "pull order"
[[ -f "$ROOT/pulled/job.log" ]] || fail "pull log"
grep -q 'password=hunter2' "$ROOT/pulled/job.log" || fail "pull should copy the log bytes as stored"

bad=$(mktemp --suffix=.md)
cat > "$bad" <<'EOF'
---
id: bad-sha
sha256: 1111111111111111111111111111111111111111111111111111111111111111
steps:
  - id: s
    mode: read-only
    summary: read
---
nope
EOF
set +e
"$HELPER" push "$bad"
push_bad=$?
set -e
[[ "$push_bad" -ne 0 ]] || fail "bad sha was pushed"

set +e
"$HELPER" wait example-readonly 1
wait_code=$?
set -e
[[ "$wait_code" -eq 4 ]] || fail "wait exit $wait_code"

echo "PASS remote helper"
rm -rf "$ROOT" "$bad"
