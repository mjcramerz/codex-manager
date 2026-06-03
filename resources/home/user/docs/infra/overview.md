# Infrastructure overview
Guidance for infrastructure automation and orchestration.


## Contents
<!-- BEGIN:contents -->
- `$CODEX_HOME/docs/infra/ansible.md` — Ansible
- `$CODEX_HOME/docs/infra/kubernetes.md` — Kubernetes
- `$CODEX_HOME/docs/infra/terraform.md` — Terraform
<!-- END:contents -->


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Scope
- Infrastructure as Code (Terraform)
- Configuration management (Ansible)
- Orchestration (Kubernetes)

## Safety baseline
- Plan before apply; review diffs and lock state.
- Prefer least privilege and scoped credentials.
- Treat state files and inventories as sensitive data.

## Quick map
- Terraform: `terraform.md`
- Ansible: `ansible.md`
- Kubernetes: `kubernetes.md`

See also:
- `../workflows/terraform.md`
- `../workflows/ansible.md`
- `../workflows/kubernetes.md`
- `../virtualization/overview.md`
- `$CODEX_HOME/index/domains/infra/tooling.md`
