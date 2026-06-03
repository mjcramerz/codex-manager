# Kubernetes app skeleton (overview)
Minimal manifests for a simple deployment.

## Outputs
- `namespace.yaml`
- `deployment.yaml`
- `service.yaml`
- `kustomization.yaml`

## Usage
1) Update image and labels.
2) Apply with `kubectl apply -k .`.
3) Verify with `kubectl rollout status`.

## Inputs
- Destination repository path for this template.
- Exact runtime/toolchain versions and pinning policy.
- Repository-specific values for placeholders, secrets, and host paths.

## Next steps
1) Copy files into deterministic repository paths.
2) Replace placeholders and pin versions/images before first commit.
3) Run the narrowest relevant checks (lint/test/build or dry-run) before commit.
