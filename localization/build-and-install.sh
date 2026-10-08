#!/bin/bash
# Rebuild and install this fork: apply the dictionary (idempotent) → config patch → build → install.
#
#   bash localization/build-and-install.sh
#
# If you just rebased on upstream, run `localization/apply.py --dry-run` first: keys it reports
# as "0 hits" are the strings upstream changed or added, and need a dictionary update.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOC="$REPO/localization"
cd "$REPO"

echo "== 1/4 apply the dictionary (already-applied entries simply no longer match)"
python3 "$LOC/apply.py" "$REPO" | head -3

echo "== 2/4 config patch (lang / CJK font fallback / updater endpoints)"
python3 "$LOC/patch-config.py" "$REPO"

echo "== 3/4 build (first cargo build takes ~5 min, incremental ~1 min)"
npm install
npm run build -- --bundles app

echo "== 4/4 install to /Applications"
APP="$REPO/src-tauri/target/release/bundle/macos/OMP Desktop.app"
test -d "$APP"
rm -rf "/Applications/OMP Desktop.app"
cp -R "$APP" /Applications/
xattr -dr com.apple.quarantine "/Applications/OMP Desktop.app" 2>/dev/null || true
codesign --force --sign - "/Applications/OMP Desktop.app" 2>/dev/null || true
echo "done: /Applications/OMP Desktop.app"
