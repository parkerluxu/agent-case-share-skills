# User case upload contract

Local export needs no MCP connection. Upload needs a personal Agent Case Share connection and an existing case owned by the user. Tool names here are suffixes; use the connected server's actual names.

## Environment

`create_case_environment` accepts:

| Field | Requirement |
| --- | --- |
| `caseSlug` | Exact selected case slug |
| `name` | Non-empty, at most 160 characters |
| `platform` | Lowercase platform name, at most 80 characters |
| `schemaVersion` | Literal `agent-environment/v1` |
| `manifest` | JSON object; send the manifest itself, not a file path or JSON string |
| `platformVersion`, `modelId` | Optional, at most 160 characters each |
| `summary` | Optional, at most 2,000 characters |

`manifest.agent.platform` must match `platform`. If both model IDs are supplied, `manifest.model.modelId` must match `modelId`. The server normalizes/redacts the manifest and computes the fingerprint. Use only its returned ID/fingerprint; a local hash is not a server fingerprint. Each snapshot is immutable and hidden.

## Session

`upload_case_session` accepts:

| Field | Requirement |
| --- | --- |
| `caseSlug` | Exact selected case slug |
| `title` | Non-empty, at most 200 characters |
| `platform` | Platform name, at most 80 characters |
| `transcript` | Non-empty text, at most 1,000,000 characters |
| `transcriptFormat` | `markdown` or `jsonl` |
| `environmentId` | Optional exact ID belonging to the same case |
| `modelId`, `summary` | Optional known facts / factual summary |
| `startedAt`, `endedAt` | Optional ISO timestamps, correctly ordered; use `endedAt` only for a known completed Session |
| `metadata` | Optional JSON object describing capture provenance, scope, and limitations |

JSONL has one JSON object per line. The converter uses `sequence`, `role`, `content`, optional `createdAt`, and tool fields `toolName`, `callId`, `arguments`, `output`; this is a portable convention, not a requirement that the server enforce this message schema. Do not attach raw Session files or send Base64 here. Uploading creates a hidden record.

If the transcript is too large, keep the local export and report the limit. Prepare a summary, selected interval, or explicitly requested multiple parts only within the user's chosen scope. Never silently trim to fit.

## Association and resuming

- Session-only may omit `environmentId`. It never implicitly creates an environment.
- To associate an existing snapshot, inspect `list_case_environments` / `get_case_environment` for the selected case and use its exact ID. Do not guess from a name or fingerprint.
- For both-mode, create the environment first and pass the returned ID to the Session write. Check both write tools before the first mutation.
- Keep returned object IDs and case slug in a local receipt. Before resuming after a failure, check the receipt and `list_case_environments` / `list_case_sessions` / detail tools to establish which writes succeeded. If an uncertain write cannot be identified reliably, stop and report that uncertainty instead of creating another record automatically.
- These writes have no MCP idempotency key, public-status override, update, or delete tool. Use the website for supported later record management; never switch upload protocols.
