# Infrastructure overview
Purpose: route infrastructure work to the right automation surface without mixing Terraform, Ansible, Kubernetes, and virtualization concerns.

## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/OVERVIEW.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->

## Scope
- Terraform for declarative infrastructure
- Ansible for host and service configuration
- Kubernetes for workload orchestration
- Adjacent virtualization docs for VM-centric environments

## Selection guide
- Desired-state infra with plans/state -> `terraform.md`
- Idempotent host/service configuration -> `ansible.md`
- Cluster workload lifecycle and policy -> `kubernetes.md`
- VM orchestration or host virtualization -> `../virtualization/overview.md`

## Guardrails
- Plan before apply.
- Keep secrets and state inventories scoped and protected.
- Keep provider/module/collection versions pinned and reviewable.
