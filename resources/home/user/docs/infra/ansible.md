# Ansible
Guidance for idempotent, reviewable configuration automation.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/infra/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline practices
- Prefer modules over raw shell.
- Use `check` mode for dry runs when possible.
- Keep secrets in Ansible Vault or external secret managers.
- Structure reusable logic into roles.

## Inventory & roles
- Keep inventory explicit and scoped.
- Use group vars and role defaults for safe defaults.

## Safety
- Avoid running on broad host globs without confirmation.
- Add `serial` or `max_fail_percentage` for safer rollouts.

See also:
- `overview.md`
- `../workflows/ansible.md`
- `$CODEX_HOME/templates/infra/ansible-role-skeleton/`
- `$CODEX_HOME/snippets/ansible/playbook.yml`
- `$CODEX_HOME/snippets/ansible/ansible.cfg`
- Use skill iac-ansible.
- `$CODEX_HOME/index/domains/infra/tooling.md`
- `$CODEX_HOME/index/domains/infra/ansible.md`
