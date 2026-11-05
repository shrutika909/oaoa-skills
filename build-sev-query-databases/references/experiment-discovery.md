# Automatic OpsMate experiment discovery

The only required user input is a SEV ID. Discovery is the union of the live
SEV-linked OpsMate instances and matching registered Ent experiment runs.

## Authoritative sources

1. Resolve all live cohort arms directly from the SEV:

   ```bash
   meta opsmate.instance from-sev --sev=<SEV_ID> --output=json --no-truncate
   meta opsmate.instance conversations --instance=<OM_ID> --output=json --no-truncate --columns=all
   ```

   Keep every proactive run and its stable session ID. These evaluator arms
   can have `is_experiment=false`; excluding them would lose the actual Avocado
   and Claude comparison cells shown by `/live`.

   Verify each stable session before approving the inventory:

   ```bash
   meta quality-toolkit.trajectory get --id=<SESSION_ID> --output=json --no-truncate
   ```

   Record only the response hash, byte count, command, and status in the
   inventory. Keep the raw trajectory private. A listed session that cannot be
   read is a real missing-source failure, not permission to omit that arm.
2. The maintained OAOA registry is
   `nest/apps/oa/oaoa_evaluator/lib/opsmate-trajectory-experiments.ts`.
   Discover its current experiment IDs at runtime. Do not copy them into the
   skill.
3. Export each registered experiment with:

   ```bash
   meta opsmate.experiment export-runs --experiment-id=<ID> --output=json --columns=all
   ```

4. Select the run whose incident artifact is the resolved SEV artifact. Check
   the normalized `incident.short_name` (for example `S707352`) as a fallback,
   never as an unchecked substitute for the artifact ID.

## Run-to-trajectory mapping

Treat the UI's experiment “cell” as an aggregate over arm runs. Preserve one
inventory item per matching run:

- experiment ID, registry name, generation, and label
- arm ID, name, role, and AgentRef
- incident artifact ID and SEV short name
- targeting/eval revision and timestamps
- execution platform and execution ref
- trajectory ref and logged session fallback

`agent-session://<UUID>` and `agent-session://ses_...` identify trajectory
storage. They do not identify the harness. Resolve the reader from the arm's
AgentRef/harness. UUID sessions commonly use Claude/Agent Home; `ses_` sessions
commonly use MetaCode/Avocado, but the arm remains authoritative.

For `/live/trajectories`, use the evaluator's production binding query and
preserve `(source_job_type_id, source_faas_instance_id)`. Reject reused or
ambiguous source sessions rather than guessing.

## Completeness gate

Write the inventory even when discovery fails, including commands, timestamps,
registry hash, exported experiments, failures, exclusions, and matches. Mark
discovery incomplete and stop before materialization when:

- the registry cannot be read or contains no experiments
- any registered experiment cannot be exported
- neither a registered run nor a SEV-linked live proactive run matches the SEV
- any discovered trajectory is unreadable from the production trajectory service
- a matching run lacks arm/harness identity or a usable trajectory reference
- two incident artifacts claim the same normalized SEV without resolution

