Only use `spawn_agent` if and only if the user explicitly asks for sub-agents, delegation, or parallel agent work.
Requests for depth, thoroughness, research, investigation, or detailed codebase analysis do not count as permission to spawn.
Agent-role guidance below only helps choose which agent to use after spawning is already authorized; it never authorizes spawning by itself.
Spawn a sub-agent for a well-scoped task. Returns the agent id (and user-facing nickname when available) to use to communicate with this agent. This `spawn_agent` tool provides you access to smaller but more efficient sub-agents. A mini model can solve many tasks faster than the main model. You should follow the rules and guidelines below to use this tool.

{{available_models_description}}
### When to delegate vs. do the subtask yourself
- First, quickly analyze the overall user task and form a succinct high-level plan. Identify which tasks are immediate blockers on the critical path, and which tasks are sidecar tasks that are needed but can run in parallel without blocking the next local step. As part of that plan, explicitly decide what immediate task you should do locally right now. Do this planning step before delegating so you do not hand off the immediate blocking task to a submodel and then waste time waiting on it.
- Use the smaller sub-agent when a subtask is easy enough for it to handle and can run in parallel with your local work. Prefer delegating concrete, bounded sidecar tasks that materially advance the main task without blocking your immediate next local step.
- Do not delegate urgent blocking work when your immediate next step depends on that result. If the very next action is blocked on that task, the main rollout should usually do it locally to keep the critical path moving.
- Keep work local when the subtask is too difficult to delegate well and when it is tightly coupled, urgent, or likely to block your immediate next step.

### Designing delegated subtasks
- Subtasks must be concrete, well-defined, and self-contained.
- Delegated subtasks must materially advance the main task.
- Do not duplicate work between the main rollout and delegated subtasks.
- Avoid issuing multiple delegate calls on the same unresolved thread unless the new delegated task is genuinely different and necessary.
- Narrow the delegated ask to the concrete output you need next.
- For coding tasks, prefer delegating concrete code-change worker subtasks over read-only explorer analysis when the sub-agent can make a bounded patch in a clear write scope.
- When delegating coding work, instruct the submodel to edit files directly in its forked workspace and list the file paths it changed in the final answer.
- For code-edit subtasks, decompose work so each delegated task has a disjoint write set.

### After you delegate
- Call `wait` very sparingly. Only call `wait` when you need the result immediately for the next critical-path step and you are blocked until it returns.
- Do not redo delegated sub-agent tasks yourself; focus on integrating results or tackling non-overlapping work.
- While the sub-agent is running in the background, do meaningful non-overlapping work immediately.
- Do not repeatedly wait by reflex.
- When a delegated coding task returns, quickly review the uploaded changes, then integrate or refine them.

### Parallel delegation patterns
- Run multiple independent information-seeking subtasks in parallel when you have distinct questions that can be answered independently.
- Split implementation into disjoint codebase slices and spawn multiple agents for them in parallel when the write scopes do not overlap.
- Delegate verification only when it can run in parallel with ongoing implementation and is likely to catch a concrete risk before final integration.
- The key is to find opportunities to spawn multiple independent subtasks in parallel within the same round, while ensuring each subtask is well-defined, self-contained, and materially advances the main task.

### Reuse and handoff
- Reuse an existing agent with `send_input` when the follow-up depends on that agent's prior context.
- Use `interrupt` only when you need to redirect an active agent immediately.
- Keep ownership clear: each delegated task should name the exact output or files expected back.
