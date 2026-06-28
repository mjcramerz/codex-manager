package Codex::Hook::PluginHint;

use strict;
use warnings;

use Exporter qw(import);
use File::Spec;
use JSON::PP qw(decode_json);

our @EXPORT_OK = qw(plugin_prompt_context);

sub _trim {
    my ($value) = @_;
    return '' if !defined $value || ref($value);
    $value =~ s/^\s+|\s+$//g;
    return $value;
}

sub _read_json_object {
    my ($path) = @_;
    return undef if !defined $path || !length($path) || !-f $path;
    open my $fh, '<:encoding(UTF-8)', $path or return undef;
    local $/;
    my $raw = <$fh>;
    close $fh;
    my $payload = eval { decode_json($raw) };
    return undef if $@ || ref($payload) ne 'HASH';
    return $payload;
}

sub _plugin_root {
    my ($bundle) = @_;
    my $home = _trim($ENV{CODEX_HOME});
    return '' if !length($home);
    my $cache_root = File::Spec->catdir($home, 'plugins', 'cache');
    return '' if !-d $cache_root;

    opendir my $dh, $cache_root or return '';
    my @marketplaces = sort grep {
        $_ ne '.'
          && $_ ne '..'
          && -d File::Spec->catdir($cache_root, $_)
    } readdir $dh;
    closedir $dh;

    for my $marketplace (@marketplaces) {
        my $candidate = File::Spec->catdir($cache_root, $marketplace, $bundle, 'local');
        return $candidate if -d $candidate;
    }
    return '';
}

sub _plugin_manifest {
    my ($bundle) = @_;
    my $root = _plugin_root($bundle);
    return ('', undef) if !length($root);
    my $manifest_path = File::Spec->catfile($root, '.codex-plugin', 'plugin.json');
    return ($root, _read_json_object($manifest_path));
}

sub _child_dirs {
    my ($root, $child) = @_;
    return () if !defined $root || !length($root);
    my $dir = File::Spec->catdir($root, $child);
    return () if !-d $dir;
    opendir my $dh, $dir or return ();
    my @names = sort grep {
        $_ ne '.'
          && $_ ne '..'
          && -d File::Spec->catdir($dir, $_)
    } readdir $dh;
    closedir $dh;
    return @names;
}

sub _plugin_apps {
    my ($root) = @_;
    my $payload = _read_json_object(File::Spec->catfile($root, '.app.json'));
    return () if ref($payload) ne 'HASH' || ref($payload->{apps}) ne 'HASH';
    return sort grep { length($_) } keys %{ $payload->{apps} };
}

sub _plugin_mcp_servers {
    my ($root) = @_;
    my $payload = _read_json_object(File::Spec->catfile($root, '.mcp.json'));
    return () if ref($payload) ne 'HASH' || ref($payload->{mcpServers}) ne 'HASH';
    return sort grep { length($_) } keys %{ $payload->{mcpServers} };
}

sub _manifest_keywords {
    my ($manifest) = @_;
    return () if ref($manifest) ne 'HASH';
    my $keywords = $manifest->{keywords};
    return () if ref($keywords) ne 'ARRAY';
    return grep { defined($_) && !ref($_) && length _trim($_) } @{$keywords};
}

sub _alias_tokens {
    my ($bundle) = @_;
    my %aliases = (
        'codex-runtime' => [qw(installer runtime hooks hooks.json codex-mcp marketplace requirements)],
        'codex-repo' => [qw(codex-rs cargo crate tui rust workspace)],
        'openai-apps' => [qw(chatgpt apps sdk widget csp mcp openai-docs)],
        'github' => [qw(pr pull-request review-comments actions workflow gh)],
        'gitlab' => [qw(merge-request pipeline gitlab-ci cicd)],
        'linear' => [qw(issue issues roadmap triage)],
        'google-calendar' => [qw(calendar event schedule availability meeting)],
        'notion' => [qw(page database wiki notes documentation meeting)],
        'obsidian' => [qw(vault note notes markdown knowledge)],
        'health-planning' => [qw(adhd cbt planner worksheet routine check-in)],
        'backend' => [qw(axum fastapi aspnet api service backend)],
        'frontend' => [qw(react nextjs nuxt sveltekit vue htmx html frontend)],
        'design-ui' => [qw(design ui ux accessibility review)],
        'browser-automation' => [qw(playwright browser screenshot electron automation)],
        'document-artifacts' => [qw(docx pdf slides pptx spreadsheet xlsx notebook ipynb)],
        'adobe-acrobat' => [qw(acrobat pdf form comment review sign signature)],
        'adobe-photoshop' => [qw(photoshop retouch composite layer image-edit)],
        'adobe-express' => [qw(express social campaign flyer visual)],
        'ai-media' => [qw(imagegen sora speech transcribe voice audio video)],
        'vercel' => [qw(vercel deploy preview production)],
        'hosting-platforms' => [qw(vercel render netlify hosting platform deploy)],
        'web-browser-linux' => [qw(browser librewolf mullvad thorium wayland labwc desktop-entry)],
        'iac' => [qw(terraform ansible iac infrastructure)],
        'containers' => [qw(docker podman compose buildx container)],
        'kubernetes' => [qw(kubernetes k8s helm manifest cluster)],
        'system-infra' => [qw(grub kernel sysctl systemd logrotate storage)],
        'virtualization' => [qw(proxmox virsh qemu kvm libvirt vm virtualization)],
        'observability' => [qw(elasticsearch kibana logstash sentry observability)],
        'security-controls' => [qw(appsec crowdsec auditd aide usbguard bitwarden)],
        'security-labs' => [qw(offsec c2 purple-team nethunter mobile wireless)],
        'cloudflare-workers' => [qw(cloudflare workers durable-objects r2 d1 queues workflows)],
        'wrangler' => [qw(wrangler cloudflare deploy bindings workers-ai)],
        'cloudflare-agents' => [qw(agent agents-sdk mcp-server durable websocket workflow)],
        'huggingface' => [qw(huggingface gradio dataset evaluation jobs trainer trackio)],
        'docs-research' => [qw(docs research api-reference compare citations)],
        'stripe' => [qw(stripe payments billing subscriptions checkout webhook)],
        'microsoft-learn' => [qw(azure microsoft dotnet learn winui)],
        'jina-ai' => [qw(jina reader grounded search retrieval)],
        'atlassian' => [qw(jira confluence atlassian issue workflow)],
        'figma' => [qw(figma node frame design-to-code)],
        'vercel-ui' => [qw(composition react-best-practices react-native vercel-ui)],
        'winui' => [qw(winui xaml windows-app-sdk windows-desktop)],
        'render' => [qw(render blueprint deploy)],
        'netlify' => [qw(netlify deploy site)],
    );
    return @{ $aliases{$bundle} || [] };
}

sub _bundle_guidance {
    my ($bundle) = @_;
    my %map = (
        'codex-runtime' => [
            '- Stay in installer/runtime source-of-truth surfaces and validate with `python3 -m py_compile src/install/codex_install.py`, `make preflight`, and the local unittest suite.',
            '- Keep runtime hook, plugin manifest, and rendered config changes aligned in one turn instead of patching one output surface in isolation.',
        ],
        'codex-repo' => [
            '- Keep Codex source-tree work crate-scoped and avoid widening beyond the touched runtime contract boundary.',
            '- Prefer the smallest `cargo check` or `cargo test` command that proves the change in the touched crate.',
        ],
        'openai-apps' => [
            '- Use official OpenAI docs first for Apps SDK, MCP app metadata, and widget/CSP behavior.',
            '- Keep MCP server, tool descriptors, and widget surface changes aligned instead of patching only one layer.',
        ],
        'github' => [
            '- Confirm `gh` auth and map fixes to one PR comment, one failing check, or one workflow boundary at a time.',
            '- Read the current review thread or failing Actions log before editing files or drafting replies.',
        ],
        'gitlab' => [
            '- Inspect the exact GitLab pipeline or include boundary before widening into adjacent delivery templates.',
            '- Keep `.gitlab-ci.yml` and shared CI-template changes deterministic and scoped to the failing job path.',
        ],
        'linear' => [
            '- Tie the work to the exact Linear issue, project, or workflow state you are changing before widening scope.',
            '- Prefer explicit issue ids, status transitions, and owner changes over broad workspace triage.',
        ],
        'google-calendar' => [
            '- Keep changes scoped to one event or one availability question at a time.',
            '- Confirm timezone, date, and attendee intent before creating or moving calendar events.',
        ],
        'notion' => [
            '- Target the exact Notion page, database, or documentation artifact instead of broad workspace cleanup.',
            '- Keep capture, research, and spec-to-implementation work tied to one durable Notion output.',
        ],
        'obsidian' => [
            '- Keep note updates scoped to one vault artifact, index, or linked task boundary at a time.',
            '- Prefer structured note capture and explicit links over broad markdown rewrites.',
        ],
        'health-planning' => [
            '- Keep health-planning outputs practical, bounded, and artifact-focused rather than drifting into generic advice.',
            '- Prefer one planner, worksheet, or check-in template per task with concrete sections and printable structure.',
        ],
        'backend' => [
            '- Anchor backend work to the exact framework boundary (`axum`, `fastapi`, or `aspnet-core`) before editing code.',
            '- Prefer typed interfaces, request validation, and narrow endpoint tests over broad service rewrites.',
        ],
        'frontend' => [
            '- Anchor frontend work to the exact framework boundary (`react`, `nextjs`, `nuxt`, `sveltekit`, `vue`, `htmx`, or plain HTML).',
            '- Prefer one route, component, or interaction boundary at a time, with accessibility and state flow checked explicitly.',
        ],
        'design-ui' => [
            '- Treat UI review as a concrete guideline audit: cite the exact interaction, readability, accessibility, or spacing issue you are fixing.',
            '- Avoid drifting from a design review into unrelated application logic unless the design issue requires it.',
        ],
        'browser-automation' => [
            '- Keep browser automation scoped to one page flow, selector set, or screenshot target at a time.',
            '- Prefer deterministic navigation and state checks over long exploratory browser sessions.',
        ],
        'document-artifacts' => [
            '- Keep document work artifact-specific: one `.docx`, `.pdf`, `.pptx`, spreadsheet, or notebook boundary at a time.',
            '- Preserve editable output and validate rendering or structure after modifying document artifacts.',
        ],
        'adobe-acrobat' => [
            '- Keep Acrobat work scoped to one PDF workflow such as read, review, fill, sign, or compare.',
            '- Preserve field, comment, and signature intent explicitly instead of flattening the document workflow.',
        ],
        'adobe-photoshop' => [
            '- Keep Photoshop work scoped to one retouching or compositing objective instead of broad visual restyling.',
            '- Preserve export intent, layers, and target asset dimensions when changing image content.',
        ],
        'adobe-express' => [
            '- Keep Adobe Express work scoped to one social asset, flyer, or campaign output at a time.',
            '- Preserve the publishing target and size/orientation assumptions explicitly.',
        ],
        'ai-media' => [
            '- Keep media generation work scoped to one modality (`imagegen`, `sora`, `speech`, or `transcribe`) and one output target at a time.',
            '- Confirm prompt, input asset, and output format before widening into batch variants.',
        ],
        'vercel' => [
            '- Keep Vercel work scoped to one deployment path: local config, preview deploy, or production deploy.',
            '- Confirm project linkage and environment intent before changing deployment settings.',
        ],
        'hosting-platforms' => [
            '- Choose the host first (`vercel`, `render`, or `netlify`) before widening into deployment implementation details.',
            '- Keep comparisons concise and implementation steps provider-specific once a target platform is known.',
        ],
        'web-browser-linux' => [
            '- Keep browser and desktop work tied to the exact browser, launcher, or Wayland workflow you are modifying.',
            '- Validate the exact browser-hardening or desktop-entry target instead of broad desktop cleanup.',
        ],
        'iac' => [
            '- Anchor IaC work to the exact tool boundary (`terraform` or `ansible`) and the smallest module or role that owns the change.',
            '- Prefer plan-safe, idempotent changes over broad configuration churn.',
        ],
        'containers' => [
            '- Keep container work scoped to one image, Dockerfile, Compose stack, or runtime boundary at a time.',
            '- Preserve reproducible build inputs and least-privilege runtime assumptions.',
        ],
        'kubernetes' => [
            '- Keep Kubernetes work scoped to the exact manifest, workload, or cluster operation boundary you are changing.',
            '- Prefer explicit resource, namespace, and probe changes over broad chart churn.',
        ],
        'system-infra' => [
            '- Keep system infrastructure work tied to the exact subsystem (`grub`, `kernel`, `sysctl`, `systemd`, `logrotate`, or storage) before editing.',
            '- Preserve rollback-aware behavior and validate only the touched subsystem boundary first.',
        ],
        'virtualization' => [
            '- Keep virtualization work tied to the exact hypervisor or VM interface (`proxmox`, `virsh`, `qemu`, `libvirt`).',
            '- Prefer explicit VM, storage, and network boundaries over broad host-wide changes.',
        ],
        'observability' => [
            '- Keep observability work scoped to the exact stack boundary (`elasticsearch`, `kibana`, `logstash`, or `sentry`).',
            '- Prefer one ingest, dashboard, retention, or issue-analysis path at a time.',
        ],
        'security-controls' => [
            '- Keep security-control changes least-privilege and tightly scoped to the exact control family you are editing.',
            '- Prefer evidence-backed hardening over speculative security churn.',
        ],
        'security-labs' => [
            '- Treat security-lab work as scoped simulation or defense engineering; keep target systems, tooling, and boundaries explicit.',
            '- Avoid broadening into unrelated offensive or host-modification steps when one lab scenario is enough.',
        ],
        'cloudflare-workers' => [
            '- Anchor Cloudflare work to the exact product boundary (`workers`, `durable-objects`, `r2`, `d1`, `queues`, `workflows`) before editing.',
            '- Prefer one Worker binding, route, or runtime concern at a time and validate against Cloudflare-specific constraints.',
        ],
        'wrangler' => [
            '- Keep `wrangler` work scoped to the exact deploy, dev, secret, or binding command path you need next.',
            '- Confirm the Worker/account boundary before running deployment-oriented changes.',
        ],
        'cloudflare-agents' => [
            '- Keep Cloudflare Agents work tied to the exact agent or remote MCP-server flow you are implementing.',
            '- Preserve state, workflow, and real-time boundaries explicitly instead of broad platform refactors.',
        ],
        'huggingface' => [
            '- Keep Hugging Face work scoped to the exact surface: Hub CLI, dataset, evaluation, jobs, training, or Gradio UI.',
            '- Confirm whether the task is local artifact work or remote Hub/Jobs work before widening scope.',
        ],
        'docs-research' => [
            '- Keep docs research tied to the exact API, official source set, or implementation question being answered.',
            '- Prefer direct source comparison and one concrete engineering conclusion over broad documentation summary.',
        ],
        'stripe' => [
            '- Keep Stripe work scoped to the exact flow: payments, billing, subscriptions, invoicing, or webhooks.',
            '- Confirm customer-impacting state changes and webhook semantics before mutating code or settings.',
        ],
        'microsoft-learn' => [
            '- Use Microsoft Learn as the primary source and keep implementation guidance tied to the exact Azure or Microsoft workload.',
            '- Prefer one service boundary and one official code or docs path at a time.',
        ],
        'jina-ai' => [
            '- Keep Jina AI work scoped to the exact search, retrieval, or reader workflow rather than general web research.',
            '- Prefer one grounded source pipeline and one implementation question per step.',
        ],
        'atlassian' => [
            '- Keep Atlassian work tied to the exact Jira or Confluence workflow being changed.',
            '- Prefer one issue flow, page flow, or integration boundary at a time.',
        ],
        'figma' => [
            '- Keep Figma work tied to the exact file, frame, or node boundary and preserve design-to-code fidelity.',
            '- Pull the smallest design context that proves the next implementation step instead of broad canvas export.',
        ],
        'vercel-ui' => [
            '- Keep Vercel UI guidance tied to the exact React composition, performance, or React Native concern in the prompt.',
            '- Prefer one component-system or rendering boundary at a time.',
        ],
        'winui' => [
            '- Keep WinUI work tied to the exact Windows App SDK, XAML, or navigation boundary you are implementing.',
            '- Preserve desktop-specific windowing, accessibility, and packaging assumptions explicitly.',
        ],
        'render' => [
            '- Keep Render work scoped to the exact blueprint, service, or deployment target you are changing.',
            '- Confirm whether the task is dashboard setup, `render.yaml`, or deploy troubleshooting before widening scope.',
        ],
        'netlify' => [
            '- Keep Netlify work scoped to the exact site linkage, preview deploy, or production deploy boundary.',
            '- Confirm build command, publish dir, and environment intent before widening into unrelated hosting changes.',
        ],
    );
    return @{ $map{$bundle} || [] };
}

sub _signal_tokens {
    my ($bundle, $manifest, $root) = @_;
    my %seen;
    my @tokens;
    my @sources = (
        $bundle,
        _trim($manifest->{name}),
        _trim((ref($manifest->{interface}) eq 'HASH' ? $manifest->{interface}->{displayName} : undef)),
        _manifest_keywords($manifest),
        _child_dirs($root, 'skills'),
        _plugin_apps($root),
        _plugin_mcp_servers($root),
        _alias_tokens($bundle),
    );
    for my $raw (@sources) {
        next if !defined $raw || ref($raw);
        my $value = lc _trim($raw);
        next if !length($value);
        $value =~ s/[^a-z0-9]+/ /g;
        $value =~ s/\s+/ /g;
        $value =~ s/^\s+|\s+$//g;
        next if !length($value) || length($value) < 3;
        next if $seen{$value}++;
        push @tokens, $value;
    }
    return @tokens;
}

sub _prompt_matches_bundle {
    my ($prompt, $bundle, $manifest, $root) = @_;
    return 0 if !length($prompt);

    my $normalized = lc($prompt);
    $normalized =~ s/[^a-z0-9]+/ /g;
    $normalized =~ s/\s+/ /g;

    my @tokens = _signal_tokens($bundle, $manifest, $root);
    return 0 if !@tokens;

    my $score = 0;
    for my $token (@tokens) {
        next if !length($token);
        if ($normalized =~ /\b\Q$token\E\b/) {
            my $weight = scalar(split / /, $token);
            $score += $weight > 0 ? $weight : 1;
            return 1 if $score >= 2;
        }
    }
    return 0;
}

sub plugin_prompt_context {
    my (%args) = @_;
    my $bundle = _trim($args{bundle});
    my $prompt = _trim($args{prompt});
    return undef if !length($bundle) || !length($prompt);

    my ($root, $manifest) = _plugin_manifest($bundle);
    return undef if !length($root) || ref($manifest) ne 'HASH';
    return undef if !_prompt_matches_bundle($prompt, $bundle, $manifest, $root);

    my $name = _trim($manifest->{name}) || $bundle;
    my $description = _trim($manifest->{description});
    my $interface = ref($manifest->{interface}) eq 'HASH' ? $manifest->{interface} : {};
    my $display_name = _trim($interface->{displayName}) || $name;

    my @lines = ("$display_name plugin context:");
    push @lines, "- Bundle scope: $description" if length($description);
    push @lines, _bundle_guidance($bundle);
    push @lines, '- Keep the next step inside this plugin family before widening into unrelated bundles.';

    return join("\n", @lines);
}

1;
