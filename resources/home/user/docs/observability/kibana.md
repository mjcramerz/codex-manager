# Kibana
Guidance for secure Kibana configuration and dashboard hygiene.


## Navigation
<!-- BEGIN:nav -->
- Parent: `$CODEX_HOME/docs/observability/overview.md`
- Pack index: `$CODEX_HOME/INDEX.md`
- Routing guide: `$CODEX_HOME/index/OVERVIEW.md`
<!-- END:nav -->


## Baseline practices
- Use spaces to separate environments or teams.
- Scope access with roles; avoid broad admin access.
- Keep saved objects under version control when possible.

## Operations
- Keep dashboards lightweight; avoid unbounded queries.
- Audit access for sensitive datasets.

See also:
- `overview.md`
- `elasticsearch.md`
- `logstash.md`
- `../workflows/elastic-stack.md`
- `$CODEX_HOME/snippets/elastic/kibana.yml`
- `$CODEX_HOME/templates/observability/elastic-stack-compose/`
- Use skill obs-kibana.
- `$CODEX_HOME/index/domains/observability/stack.md`
- `$CODEX_HOME/index/domains/observability/kibana.md`
