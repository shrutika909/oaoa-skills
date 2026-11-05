# Skill folder guide

Start with `SKILL.md`, then use this map:

| Folder | Contents | Use |
|---|---|---|
| `examples/` | Forwarding prompt and document example | Start or explain a trial run |
| `references/` | Workflow, staging, output, anonymization, and LogView contracts | Follow the authoring rules |
| `assets/` | Policy, fallback template, five ToolSpecs, and safe example manifests | Generate consistent artifacts |
| `scripts/` | Reconstruction, scaffold, replay, CLI, and clients | Build and operate the component |
| `man/` | CLI manual page | Understand the agent-visible interface |
| `tests/` | Package, synthetic, replay, receipt, and container tests | Validate changes before sharing |
| `docs/` | Design-document addenda | Review design context without loading it at runtime |

## Suggested reading order

1. `SKILL.md`
2. `references/workflow.md`
3. `references/staging-contract.md`
4. `references/anonymization-contract.md`
5. `references/output-contract.md`
6. `references/logview-contract.md` when LogView evidence is present
7. `references/autopilot-integration.md` for complete-task handoff
8. `examples/PROMPT_S707352.md` for the example trial

## Generated output layout

- `replay/`: SQLite, reconstruction SQL, replay server, server ToolSpecs, and startup script
- `task/`: five named CLIs, client, safe ToolSpecs, man pages, manifests, and validation results; no database snapshot
- `private/`: build report, authoring manifest, mappings, receipts, and transformation state
- `scaffolding_summary.json`: safe handoff to the parent task scaffolder

Do not copy `private/` into the task-solving agent environment.
