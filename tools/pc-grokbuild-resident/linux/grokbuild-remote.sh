#!/usr/bin/env bash
# Push an order to the PC inbox, poll one status file, approve or deny, pull results.
# Remote work is a short PowerShell script. This file does not open a browser.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
STAMP="$SCRIPT_DIR/order_stamp.py"
SHOW=0

usage() {
  cat <<'EOF'
Usage:
  grokbuild-remote.sh push <order.md>
  grokbuild-remote.sh status <job-id>
  grokbuild-remote.sh wait <job-id> [timeout-sec]
  grokbuild-remote.sh approve <job-id>
  grokbuild-remote.sh deny <job-id>
  grokbuild-remote.sh pull <job-id> <dest-dir>
  grokbuild-remote.sh show <push|status|approve|deny|pull> [args...]

On the Linux box, point one function at the PC and export it:

  grokbuild_pc() {
    ssh -o BatchMode=yes hp@LAPTOP-PL4TICBO \
      powershell.exe -NoProfile -NonInteractive -EncodedCommand "$1"
  }
  export -f grokbuild_pc
  export GROKBUILD_RSH_FUNC=grokbuild_pc

The EncodedCommand value is UTF-16LE PowerShell. status/approve/deny/pull are one
round trip. push is one round trip with the order inlined.

Local test without a PC:

  export GROKBUILD_LOCAL=1
  export GROKBUILD_ROOT=/tmp/grokbuild-test

On the PC, leave GROKBUILD_ROOT unset. The scripts then use
C:\Users\hp\Documents\grokbuild.
EOF
}

die() {
  echo "$*" >&2
  exit 2
}

need_id() {
  local id="$1"
  [[ "$id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$ ]] || die "bad job id: $id"
}

prelude() {
  cat <<'EOF'
$ErrorActionPreference = 'Stop'
$root = $env:GROKBUILD_ROOT
if ([string]::IsNullOrWhiteSpace($root)) {
  if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    $root = Join-Path (Join-Path $env:USERPROFILE 'Documents') 'grokbuild'
  } else {
    $root = 'C:\Users\hp\Documents\grokbuild'
  }
}
$queue = Join-Path $root 'queue'
EOF
}

run_ps() {
  local script="$1"
  if [[ "$SHOW" == 1 ]]; then
    printf '%s\n' "$script"
    return 0
  fi
  if [[ "${GROKBUILD_LOCAL:-}" == 1 ]]; then
    local tmp code
    tmp=$(mktemp)
    printf '%s\n' "$script" > "$tmp"
    set +e
    pwsh -NoProfile -NonInteractive -File "$tmp"
    code=$?
    set -e
    rm -f "$tmp"
    return "$code"
  fi
  [[ -n "${GROKBUILD_RSH_FUNC:-}" ]] || die "set GROKBUILD_RSH_FUNC or GROKBUILD_LOCAL=1"
  local enc
  enc=$(printf '%s' "$script" | python3 -c 'import sys,base64; sys.stdout.write(base64.b64encode(sys.stdin.buffer.read().decode("utf-8").encode("utf-16le")).decode("ascii"))')
  if [[ ${#enc} -gt 24000 ]]; then
    die "PowerShell script is too long for EncodedCommand"
  fi
  "$GROKBUILD_RSH_FUNC" "$enc"
}

script_status() {
  local id="$1"
  cat <<EOF
$(prelude)
\$id = '${id}'
if (\$id -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,80}\$') { throw 'bad job id' }
\$path = Join-Path (Join-Path \$queue 'status') (\$id + '.json')
if (-not [System.IO.File]::Exists(\$path)) {
  [Console]::Out.WriteLine('{"id":"' + \$id + '","state":"missing"}')
  exit 0
}
[Console]::Out.Write([System.IO.File]::ReadAllText(\$path))
[Console]::Out.WriteLine('')
EOF
}

script_approve() {
  local id="$1"
  cat <<EOF
$(prelude)
\$id = '${id}'
if (\$id -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,80}\$') { throw 'bad job id' }
\$dir = Join-Path \$queue 'confirm'
[void][System.IO.Directory]::CreateDirectory(\$dir)
\$json = Join-Path \$dir (\$id + '.json')
\$ok = Join-Path \$dir (\$id + '.ok')
\$ng = Join-Path \$dir (\$id + '.ng')
if (-not [System.IO.File]::Exists(\$json)) {
  [Console]::Error.WriteLine('confirm json not found')
  exit 3
}
if ([System.IO.File]::Exists(\$ng)) {
  [Console]::Error.WriteLine('deny file already exists')
  exit 3
}
\$utf8 = New-Object System.Text.UTF8Encoding \$false
[System.IO.File]::WriteAllText(\$ok, '{"decision":"ok","job_id":"' + \$id + '"}', \$utf8)
[Console]::Out.WriteLine(\$ok)
EOF
}

script_deny() {
  local id="$1"
  cat <<EOF
$(prelude)
\$id = '${id}'
if (\$id -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,80}\$') { throw 'bad job id' }
\$dir = Join-Path \$queue 'confirm'
[void][System.IO.Directory]::CreateDirectory(\$dir)
\$ok = Join-Path \$dir (\$id + '.ok')
\$ng = Join-Path \$dir (\$id + '.ng')
if ([System.IO.File]::Exists(\$ok)) {
  [Console]::Error.WriteLine('approve file already exists')
  exit 3
}
\$utf8 = New-Object System.Text.UTF8Encoding \$false
[System.IO.File]::WriteAllText(\$ng, '{"decision":"ng","job_id":"' + \$id + '"}', \$utf8)
[Console]::Out.WriteLine(\$ng)
EOF
}

script_push() {
  local job_id="$1"
  local remote_name="$2"
  local b64="$3"
  cat <<EOF
$(prelude)
\$id = '${job_id}'
\$name = '${remote_name}'
if (\$name -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*\.md\$') { throw 'bad file name' }
\$inbox = Join-Path \$queue 'inbox'
[void][System.IO.Directory]::CreateDirectory(\$inbox)
\$dest = Join-Path \$inbox \$name
if ([System.IO.File]::Exists(\$dest)) { throw 'inbox already has that file' }
\$b64 = @'
${b64}
'@
\$bytes = [Convert]::FromBase64String((\$b64 -replace '\s',''))
\$tmp = \$dest + '.partial'
[System.IO.File]::WriteAllBytes(\$tmp, \$bytes)
[System.IO.File]::Move(\$tmp, \$dest)
[Console]::Out.WriteLine('id=' + \$id)
[Console]::Out.WriteLine('file=' + \$name)
EOF
}

script_pull() {
  local id="$1"
  cat <<EOF
$(prelude)
\$id = '${id}'
if (\$id -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,80}\$') { throw 'bad job id' }
function Emit-File(\$label, \$path) {
  if (-not [System.IO.File]::Exists(\$path)) { return }
  \$bytes = [System.IO.File]::ReadAllBytes(\$path)
  \$b64 = [Convert]::ToBase64String(\$bytes)
  [Console]::Out.WriteLine('##FILE ' + \$label)
  [Console]::Out.WriteLine('##B64 ' + \$b64)
}
\$status = Join-Path (Join-Path \$queue 'status') (\$id + '.json')
if (-not [System.IO.File]::Exists(\$status)) {
  [Console]::Error.WriteLine('status not found')
  exit 3
}
Emit-File 'status.json' \$status
\$raw = [System.IO.File]::ReadAllText(\$status)
\$obj = \$raw | ConvertFrom-Json
\$leaf = [System.IO.Path]::GetFileName([string]\$obj.order_file)
if (\$leaf -match '^[A-Za-z0-9][A-Za-z0-9._-]*\.md\$') {
  foreach (\$bucket in @('done','failed','running')) {
    \$candidate = Join-Path (Join-Path \$queue \$bucket) \$leaf
    if ([System.IO.File]::Exists(\$candidate)) {
      Emit-File 'order.md' \$candidate
      break
    }
  }
}
Emit-File 'job.log' (Join-Path (Join-Path \$queue 'logs') (\$id + '.log'))
[Console]::Out.WriteLine('##END')
EOF
}

cmd_status() {
  need_id "$1"
  run_ps "$(script_status "$1")"
}

cmd_approve() {
  need_id "$1"
  run_ps "$(script_approve "$1")"
}

cmd_deny() {
  need_id "$1"
  run_ps "$(script_deny "$1")"
}

cmd_push() {
  local src="$1"
  [[ -f "$src" ]] || die "order not found: $src"
  local base
  base=$(basename -- "$src")
  [[ "$base" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*\.md$ ]] || die "order file name must be a simple .md name"
  local stamped_file job_id ts remote_name b64
  stamped_file=$(mktemp)
  python3 "$STAMP" stamp "$src" > "$stamped_file"
  job_id=$(python3 -c 'import re,sys,pathlib; t=pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"); m=re.search(r"(?m)^id:\s*(\S+)\s*$", t); print(m.group(1) if m else "")' "$stamped_file")
  need_id "$job_id"
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  remote_name="${ts}-${base}"
  [[ "$remote_name" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*\.md$ ]] || die "remote name rejected"
  b64=$(python3 -c 'import base64,pathlib,sys; sys.stdout.write(base64.b64encode(pathlib.Path(sys.argv[1]).read_bytes()).decode("ascii"))' "$stamped_file")
  rm -f "$stamped_file"
  run_ps "$(script_push "$job_id" "$remote_name" "$b64")"
}

decode_pull() {
  local dest="$1"
  # python -c keeps stdin on the pipe. A heredoc would replace that stdin.
  python3 -c '
import base64, pathlib, sys
dest = pathlib.Path(sys.argv[1])
label = None
saw_end = False
for line in sys.stdin:
    line = line.rstrip("\n")
    if line.startswith("##FILE "):
        label = line[7:]
        if label not in ("status.json", "order.md", "job.log"):
            raise SystemExit("unexpected file label: %s" % label)
    elif line.startswith("##B64 "):
        if label is None:
            raise SystemExit("b64 without file")
        (dest / label).write_bytes(base64.b64decode(line[6:]))
        label = None
    elif line == "##END":
        saw_end = True
        break
if not saw_end:
    raise SystemExit("pull stream missing END")
if not (dest / "status.json").is_file():
    raise SystemExit("status.json missing")
' "$dest"
}

cmd_pull() {
  local id="$1"
  local dest="$2"
  need_id "$id"
  if [[ "$SHOW" == 1 ]]; then
    run_ps "$(script_pull "$id")"
    return 0
  fi
  mkdir -p "$dest"
  run_ps "$(script_pull "$id")" | decode_pull "$dest"
}

cmd_wait() {
  local id="$1"
  local timeout="${2:-600}"
  [[ "$timeout" =~ ^[0-9]+$ ]] || die "bad timeout"
  need_id "$id"
  if [[ "$SHOW" == 1 ]]; then
    run_ps "$(script_status "$id")"
    return 0
  fi
  local start now json state hinted
  start=$(date +%s)
  hinted=0
  while true; do
    json=$(cmd_status "$id")
    state=$(printf '%s' "$json" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("state",""))')
    case "$state" in
      done|denied|aborted|failed|rejected)
        printf '%s\n' "$json"
        return 0
        ;;
      awaiting_confirm)
        if [[ "$hinted" -eq 0 ]]; then
          echo "awaiting_confirm: read confirm/${id}.json then approve or deny" >&2
          hinted=1
        fi
        ;;
    esac
    now=$(date +%s)
    if (( now - start >= timeout )); then
      echo "timeout waiting for ${id}" >&2
      return 4
    fi
    sleep 2
  done
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

cmd="$1"
shift
if [[ "$cmd" == "show" ]]; then
  SHOW=1
  [[ $# -ge 1 ]] || die "show needs a command"
  cmd="$1"
  shift
fi

case "$cmd" in
  push)
    [[ $# -eq 1 ]] || die "push needs one order file"
    cmd_push "$1"
    ;;
  status)
    [[ $# -eq 1 ]] || die "status needs a job id"
    cmd_status "$1"
    ;;
  wait)
    [[ $# -ge 1 && $# -le 2 ]] || die "wait needs a job id"
    cmd_wait "$@"
    ;;
  approve)
    [[ $# -eq 1 ]] || die "approve needs a job id"
    cmd_approve "$1"
    ;;
  deny)
    [[ $# -eq 1 ]] || die "deny needs a job id"
    cmd_deny "$1"
    ;;
  pull)
    [[ $# -eq 2 ]] || die "pull needs a job id and a dest dir"
    cmd_pull "$1" "$2"
    ;;
  *)
    usage
    exit 2
    ;;
esac
