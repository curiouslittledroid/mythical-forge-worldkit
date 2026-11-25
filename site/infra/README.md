# Deploying the site

Static Astro output in a **private S3 bucket**, read through **CloudFront** (OAC). No server, no
container, no database. The codex repository stays private; only `site/dist` is uploaded.

**The world's own ids live in `site/infra/state.json`** (bucket, OAC, distribution, function, deploy
role, URL — not secret), written by `bootstrap.sh`. This document is the process; the values below
are placeholders to substitute. A world records the result in its own site note.

- **Region:** whichever it is created in (`AWS_REGION`); this deployment uses `ap-southeast-2`.

## One-time setup

```bash
./site/infra/bootstrap.sh          # bucket, OAC, distribution, bucket policy (idempotent)
./site/infra/bootstrap.sh --status # what exists, and the site URL
```

Then the GitHub side, once:

```bash
# repository variables (Settings -> Variables, or:)
gh variable set AWS_DEPLOY_ROLE_ARN        --body "arn:aws:iam::<account-id>:role/<world>-site-deploy"
gh variable set AWS_REGION                 --body "ap-southeast-2"
gh variable set SITE_BUCKET                --body "<world>-site"
gh variable set CLOUDFRONT_DISTRIBUTION_ID --body "<distribution-id>"
gh variable set SITE_URL                   --body "https://<distribution-hostname>"
```

### The deploy role

`<world>-site-deploy` — a role for **this repository only**, created by `bootstrap.sh`. It cannot
do anything except publish this site:

| | |
|---|---|
| Trust | OIDC `token.actions.githubusercontent.com`, `aud` = `sts.amazonaws.com`, `sub` = `repo:<owner>@<owner-id>/<repo>@<repo-id>:environment:production`, `ref` = `refs/heads/main` |
| Permissions | `s3:ListBucket` on the bucket; `s3:Get/Put/DeleteObject` on its objects; `cloudfront:CreateInvalidation` on this one distribution |
| Session | 1 hour |

Consequences worth knowing:

- The workflow's deploy job must run in the **`production`** environment and from **`main`**;
  `workflow_dispatch` runs from any other branch will be denied. That is deliberate.
- It deliberately does **not** use `GitHubActionsDeployRole-dev`. That role is CDK-managed in
  `mythical-forge/bootstrap/oidc-setup`, scoped to that repository, and an earlier attempt to share
  it meant hand-editing a CDK-owned trust policy — which the next `cdk deploy` would have reverted.

### Optional: make deploys wait for a second human

`meta/site.md` says a build may deploy only after the audit has been read. Every run prints that
audit to its summary, and a run must ask for `publish` to deploy at all. To add a second, blocking
approval, add required reviewers to the `production` environment:

```bash
gh api -X PUT repos/<owner>/<repo>/environments/production \
  -F 'reviewers[][type]=User' -F "reviewers[][id]=$(gh api user --jq .id)"
```

Deploys then pause after the build job until approved. Remove it with
`gh api -X DELETE repos/<owner>/<repo>/environments/production`.

## Deploying

**Publishing is manual. Nothing deploys on a push.** Every run is started by hand.

- **By hand:** Actions → *Site* → *Run workflow* (branch `main`) → tick **publish** to deploy.
- **By hand, from a terminal:**

```bash
gh workflow run site.yml                       # build only: checks, export, build, audit in the summary
gh workflow run site.yml -f publish=true       # build, then publish to CloudFront
```

- A run **without** `publish` builds the site and stops. Read the audit in the run summary (or
  `site/audit/latest.json` from a local build), then re-run with `publish` if it is clean.
- Runs from a branch other than `main` fail at the deploy job's first step: the role's trust policy
  allows `refs/heads/main` only.
- **From a workstation** (fallback, builds and publishes in one go, uses your own AWS credentials):

```bash
./site/deploy.sh
```

## Caching

| Object | `Cache-Control` |
|---|---|
| `_astro/*` (hashed) | `public,max-age=31536000,immutable` |
| `pagefind/**` except `pagefind-entry.json`, `pagefind.js` | `public,max-age=31536000,immutable` |
| everything else: HTML, images, `favicon.svg`, the two pagefind entry files | `public,max-age=0,must-revalidate` |

The distribution uses the managed **CachingOptimized** cache policy, so those headers are honoured
(bounded by MinTTL 1 s / MaxTTL 1 year). Every deploy invalidates `/*`.

## Pretty URLs

An S3 REST origin has no directory index — it looks for an object literally called
`places/<slug>/`, which never exists — so a **CloudFront viewer-request function**
(`site/infra/index-rewrite.js`) appends `index.html` to any request for a directory. `/`, `/places/<slug>/`
and `/places/<slug>` all resolve; anything with an extension (`/img/hero.jpg`, `/rss.xml`,
`/pagefind/pagefind.js`) passes through untouched. `bootstrap.sh` creates, publishes and associates it.

## Errors

403 and 404 from the origin both return `/404.html` with a 404 status, so a mistyped URL gets the
site's own page rather than an S3 XML error.

## Adding a domain later

1. Request or import an ACM certificate **in `us-east-1`** (CloudFront requirement).
2. Add the alternate domain name and certificate to the distribution.
3. Point DNS at the distribution.
4. `gh variable set SITE_URL --body "https://your.domain"` and redeploy, so canonical URLs, the RSS
   feed and the social card use it.
