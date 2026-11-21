#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
pwsh -NoProfile -File "$ROOT/Invoke-SelfTest.ps1"
bash "$ROOT/remote-helper.bash"
