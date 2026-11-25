#!/usr/bin/env bash
# One-time AWS setup for a world's site (roadmap Step 16, Phase 3).
#
#   ./site/infra/bootstrap.sh          # create or repair: bucket, OAC, distribution, policy
#   ./site/infra/bootstrap.sh --status # print what exists and what the site URL is
#
# Idempotent: safe to re-run. Writes the ids it used to site/infra/state.json (committed; not secret).
#
# What it makes:
#   - a private S3 bucket (block public access on: CloudFront reads it through an OAC)
#   - a CloudFront distribution in front, with index.html as the root object, 404 -> /404.html,
#     compression on, and the managed CachingOptimized cache policy (origin Cache-Control is honoured)
#   - a bucket policy that lets exactly that one distribution read the bucket
#
# It also creates the deploy role, scoped to this repository and to the `production` environment
# only: no shared role, and no AdministratorAccess. The role's trust policy pins the repository by
# its numeric ids, which cannot be guessed, so pass GITHUB_SUBJECT or let gh(1) resolve it here.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE="$HERE/state.json"

# --status needs no input at all: everything it prints is already recorded in state.json. It runs
# before the SITE_BUCKET requirement so that asking what exists never demands knowing the name.
if [ "${1:-}" = "--status" ]; then
  jq -r '"bucket:       \(.bucket)\ndistribution: \(.distribution_id)\nsite url:     \(.site_url)"' "$STATE" 2>/dev/null \
    || { echo "not set up yet"; exit 1; }
  exit 0
fi

# AWS_REGION is the name the workflow passes and the AWS convention; REGION is kept as an alias.
REGION="${AWS_REGION:-${REGION:-ap-southeast-2}}"
BUCKET="${SITE_BUCKET:?set SITE_BUCKET, e.g. myworld-site}"
NAME="${NAME:-$BUCKET}"

echo "== bucket $BUCKET ($REGION)"
if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "   exists"
else
  # A bucket created in us-east-1 must not pass a LocationConstraint.
  if aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
      --create-bucket-configuration "LocationConstraint=$REGION" >/dev/null 2>&1; then
    echo "   created"
  else
    BUCKET="$BUCKET-$(aws sts get-caller-identity --query Account --output text)"
    echo "   name taken; using $BUCKET"
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
      --create-bucket-configuration "LocationConstraint=$REGION" >/dev/null
    echo "   created"
  fi
fi
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-encryption --bucket "$BUCKET" \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

echo "== origin access control"
OAC_ID=$(aws cloudfront list-origin-access-controls \
  --query "OriginAccessControlList.Items[?Name=='$NAME'].Id | [0]" --output text 2>/dev/null || echo "None")
if [ -z "$OAC_ID" ] || [ "$OAC_ID" = "None" ]; then
  OAC_ID=$(aws cloudfront create-origin-access-control --origin-access-control-config \
    "Name=$NAME,Description=Player-facing world codex,SigningProtocol=sigv4,SigningBehavior=always,OriginAccessControlOriginType=s3" \
    --query 'OriginAccessControl.Id' --output text)
  echo "   created $OAC_ID"
else
  echo "   exists $OAC_ID"
fi

echo "== distribution"
DIST_ID=""
if [ -f "$STATE" ]; then
  DIST_ID=$(jq -r '.distribution_id // empty' "$STATE")
fi
if [ -n "$DIST_ID" ] && aws cloudfront get-distribution --id "$DIST_ID" >/dev/null 2>&1; then
  echo "   exists $DIST_ID"
else
  cat > /tmp/world-site-dist.json <<JSON
{
  "CallerReference": "<world>-site-$(date +%Y%m%d%H%M%S)",
  "Comment": "The world's player-facing codex",
  "Enabled": true,
  "DefaultRootObject": "index.html",
  "PriceClass": "PriceClass_All",
  "HttpVersion": "http2and3",
  "IsIPV6Enabled": true,
  "Origins": {
    "Quantity": 1,
    "Items": [{
      "Id": "s3-origin",
      "DomainName": "$BUCKET.s3.$REGION.amazonaws.com",
      "OriginPath": "",
      "S3OriginConfig": { "OriginAccessIdentity": "" },
      "OriginAccessControlId": "$OAC_ID"
    }]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "s3-origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": { "Quantity": 2, "Items": ["GET", "HEAD"], "CachedMethods": { "Quantity": 2, "Items": ["GET", "HEAD"] } },
    "Compress": true,
    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
    "OriginRequestPolicyId": "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf",
    "ResponseHeadersPolicyId": "67f7725c-6f97-4210-82d7-5512b31e9d03"
  },
  "CustomErrorResponses": {
    "Quantity": 2,
    "Items": [
      { "ErrorCode": 403, "ResponsePagePath": "/404.html", "ResponseCode": "404", "ErrorCachingMinTTL": 10 },
      { "ErrorCode": 404, "ResponsePagePath": "/404.html", "ResponseCode": "404", "ErrorCachingMinTTL": 10 }
    ]
  },
  "Restrictions": { "GeoRestriction": { "RestrictionType": "none", "Quantity": 0 } },
  "ViewerCertificate": { "CloudFrontDefaultCertificate": true }
}
JSON
  DIST_ID=$(aws cloudfront create-distribution --distribution-config file:///tmp/world-site-dist.json \
    --query 'Distribution.Id' --output text)
  echo "   created $DIST_ID"
fi

DIST_ARN=$(aws cloudfront get-distribution --id "$DIST_ID" --query 'Distribution.ARN' --output text)
DOMAIN=$(aws cloudfront get-distribution --id "$DIST_ID" --query 'Distribution.DomainName' --output text)

echo "== bucket policy (only this distribution may read)"
cat > /tmp/world-site-bucket-policy.json <<JSON
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowCloudFrontServicePrincipalRead",
    "Effect": "Allow",
    "Principal": { "Service": "cloudfront.amazonaws.com" },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::$BUCKET/*",
    "Condition": { "StringEquals": { "AWS:SourceArn": "$DIST_ARN" } }
  }]
}
JSON
aws s3api put-bucket-policy --bucket "$BUCKET" --policy file:///tmp/world-site-bucket-policy.json

echo "== URL rewrite function"
FN_NAME="$NAME-index-rewrite"
FN_CODE="$HERE/index-rewrite.js"
if aws cloudfront describe-function --name "$FN_NAME" >/dev/null 2>&1; then
  FN_ETAG=$(aws cloudfront describe-function --name "$FN_NAME" --query ETag --output text)
  aws cloudfront update-function --name "$FN_NAME" --if-match "$FN_ETAG" \
    --function-config '{"Comment":"Append index.html to directory URLs","Runtime":"cloudfront-js-2.0"}' \
    --function-code "fileb://$FN_CODE" >/dev/null
  echo "   updated"
else
  aws cloudfront create-function --name "$FN_NAME" \
    --function-config '{"Comment":"Append index.html to directory URLs","Runtime":"cloudfront-js-2.0"}' \
    --function-code "fileb://$FN_CODE" >/dev/null
  echo "   created"
fi
FN_ETAG=$(aws cloudfront describe-function --name "$FN_NAME" --query ETag --output text)
aws cloudfront publish-function --name "$FN_NAME" --if-match "$FN_ETAG" >/dev/null
FN_ARN=$(aws cloudfront describe-function --name "$FN_NAME" \
  --query 'FunctionSummary.FunctionMetadata.FunctionARN' --output text)

DIST_ETAG=$(aws cloudfront get-distribution-config --id "$DIST_ID" --query ETag --output text)
aws cloudfront get-distribution-config --id "$DIST_ID" --query DistributionConfig --output json > /tmp/world-site-dist-current.json
python3 - "$FN_ARN" <<'PYEOF'
import json, sys
arn = sys.argv[1]
cfg = json.load(open("/tmp/world-site-dist-current.json"))
cfg["DefaultCacheBehavior"]["FunctionAssociations"] = {
    "Quantity": 1,
    "Items": [{"FunctionARN": arn, "EventType": "viewer-request"}],
}
json.dump(cfg, open("/tmp/world-site-dist-updated.json", "w"), indent=2)
PYEOF
aws cloudfront update-distribution --id "$DIST_ID" --if-match "$DIST_ETAG" \
  --distribution-config file:///tmp/world-site-dist-updated.json >/dev/null
echo "   associated with $DIST_ID (the distribution redeploys in a few minutes)"

echo "== deploy role (this repository only, least privilege)"
ROLE_NAME="$NAME-deploy"
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
OIDC_ARN="arn:aws:iam::$ACCOUNT:oidc-provider/token.actions.githubusercontent.com"
# The subject names the owner and the repository by numeric id: a wrong value creates a role that
# can never be assumed, so this fails at setup rather than in CI.
SUBJECT="${GITHUB_SUBJECT:-}"
if [ -z "$SUBJECT" ] && command -v gh >/dev/null 2>&1; then
  SUBJECT=$(gh api "repos/{owner}/{repo}" \
    --jq '"repo:\(.owner.login)@\(.owner.id)/\(.name)@\(.id):environment:production"' 2>/dev/null) || SUBJECT=""
fi
: "${SUBJECT:?set GITHUB_SUBJECT (repo:owner@id/repo@id:environment:production), or run this where gh(1) can resolve the repository}"

cat > /tmp/world-site-trust.json <<JSON
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "$OIDC_ARN" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": "$SUBJECT"
      },
      "StringLike": {
        "token.actions.githubusercontent.com:ref": ["refs/heads/main"]
      }
    }
  }]
}
JSON

if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  aws iam update-assume-role-policy --role-name "$ROLE_NAME" \
    --policy-document file:///tmp/world-site-trust.json
  echo "   exists, trust refreshed"
else
  aws iam create-role --role-name "$ROLE_NAME" \
    --description "Publishes the The world's player-facing site to S3 and CloudFront" \
    --assume-role-policy-document file:///tmp/world-site-trust.json \
    --max-session-duration 3600 \
    --tags Key=Project,Value="$NAME" Key=ManagedBy,Value=site/infra/bootstrap.sh >/dev/null
  echo "   created"
fi

# Only what a deploy needs: write the bucket, invalidate this one distribution.
cat > /tmp/world-site-role-policy.json <<JSON
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListTheBucket",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::$BUCKET"
    },
    {
      "Sid": "ReadWriteObjects",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::$BUCKET/*"
    },
    {
      "Sid": "InvalidateThisDistribution",
      "Effect": "Allow",
      "Action": ["cloudfront:CreateInvalidation", "cloudfront:GetInvalidation"],
      "Resource": "$DIST_ARN"
    }
  ]
}
JSON
aws iam put-role-policy --role-name "$ROLE_NAME" \
  --policy-name "$NAME-site-deploy" --policy-document file:///tmp/world-site-role-policy.json
ROLE_ARN="arn:aws:iam::$ACCOUNT:role/$ROLE_NAME"
echo "   $ROLE_ARN"

cat > "$STATE" <<JSON
{
  "region": "$REGION",
  "bucket": "$BUCKET",
  "oac_id": "$OAC_ID",
  "distribution_id": "$DIST_ID",
  "distribution_arn": "$DIST_ARN",
  "site_url": "https://$DOMAIN",
  "function": "$FN_NAME",
  "function_arn": "$FN_ARN",
  "deploy_role_arn": "$ROLE_ARN"
}
JSON

echo
echo "region:       $REGION"
echo "deploy role:  $ROLE_ARN"
echo "bucket:       $BUCKET"
echo "distribution: $DIST_ID"
echo "site url:     https://$DOMAIN"
echo
echo "Next: set the repository variables in site/infra/README.md, then push or run the workflow."
