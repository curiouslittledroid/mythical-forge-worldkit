#!/usr/bin/env bash
# Publish the site from this machine (fallback for the GitHub Action; needs AWS credentials).
#
#   ./site/deploy.sh            # export, build, check links, upload, invalidate
#   ./site/deploy.sh --no-build # upload the existing dist/
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
STATE="$HERE/infra/state.json"
[ -f "$STATE" ] || { echo "run ./site/infra/bootstrap.sh first"; exit 1; }

BUCKET=$(jq -r .bucket "$STATE")
DIST_ID=$(jq -r .distribution_id "$STATE")
SITE_URL=$(jq -r .site_url "$STATE")

if [ "${1:-}" != "--no-build" ]; then
  ( cd "$ROOT" && python3 tools/site_export.py )
  python3 "$ROOT/tools/site_audit_report.py" --strict >/dev/null
  ( cd "$HERE" && SITE_URL="$SITE_URL" npm run build >/dev/null )
  python3 "$ROOT/tools/site_link_check.py"
fi

cd "$HERE"
aws s3 sync dist "s3://$BUCKET" --delete \
  --exclude "_astro/*" --exclude "pagefind/*" \
  --cache-control "public,max-age=0,must-revalidate"
aws s3 sync dist/_astro "s3://$BUCKET/_astro" \
  --cache-control "public,max-age=31536000,immutable"
aws s3 sync dist/pagefind "s3://$BUCKET/pagefind" \
  --exclude "pagefind-entry.json" --exclude "pagefind.js" \
  --cache-control "public,max-age=31536000,immutable"
for f in pagefind-entry.json pagefind.js; do
  aws s3 cp "dist/pagefind/$f" "s3://$BUCKET/pagefind/$f" \
    --cache-control "public,max-age=0,must-revalidate"
done
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" >/dev/null
echo "published: $SITE_URL"
