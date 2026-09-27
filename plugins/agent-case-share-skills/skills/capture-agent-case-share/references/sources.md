# Sources and local conversion

## Select sources

Use an exact Session ID/path supplied by the host or user. Inspect only enough metadata to identify a candidate when necessary. Do not read every conversation or select solely by modification time. For both-mode, selection of one Session does not authorize including other sessions or subagent transcripts.

### Codex

- Explicit configuration files can include `config.toml` and applicable project configuration. The converter parses TOML using Python 3.11+'s `tomllib`; pass multiple `--config` files in precedence order. Select a known `--profile` when applicable. This captures supplied configuration layers, not a guarantee of the effective historical setup: UI/CLI overrides and other layers may be absent.
- Local rollout JSONL commonly lives below the host's configured Codex home in `sessions` or `archived_sessions`. Locations and event formats can change. Prefer a host-provided exact path or export. Do not inspect authentication files or databases to work around unavailable history.
- The adapter reads visible `response_item` messages and function/custom-tool calls/results. It uses `event_msg` user/agent messages only when that message role has no response-item messages, preventing the common duplicated event/response transcript. It omits system/developer context, reasoning, encrypted content, and bookkeeping. `turn_context` model IDs are Session evidence; configured default models are environment evidence.
- Configured MCP servers, skill enablement overrides, and plugin entries are inventories. Skill overrides are not a complete installed-skill list; use an explicitly selected `--skill-dir` or a curated manifest when inventory is requested.

### Claude Code

- Use explicit JSON settings files, a selected `.mcp.json`, or a curated manifest. Supply files in precedence order. The adapter extracts model, `mcpServers`, and `enabledPlugins`; it omits hooks, auth data, environment-variable values, and unrelated settings. It does not infer active per-project servers from all entries in `~/.claude.json`.
- Conversation JSONL commonly lives at `~/.claude/projects/<project>/<session>.jsonl`. Read only the selected file. Large external tool-result files, images, and subagent logs are separate sources and are not automatically opened.
- The adapter reads user/assistant message text, `tool_use`, and `tool_result`. It omits thinking/redacted-thinking, binary blocks, bookkeeping, and sidechain messages, and removes duplicate UUID records. External result references remain references, not evidence that their file contents were captured.

### Generic exports and other hosts

- A `.md` / `.markdown` / `.txt` transcript is preserved as explicitly supplied text with redaction. Date/turn/message-only filters need structured data and will fail rather than pretend to filter Markdown. For a custom selection, first prepare an explicitly scoped Markdown file and label its scope in the request metadata.
- Generic JSONL accepts objects with `role` (`user`, `assistant`, `tool`) and `content`, or tool `arguments` / `output`; optional `createdAt` / `timestamp` and `toolName` / `callId` are retained. Convert a different host's documented format into this shape before using `--platform` with that host's name. Unknown message formats are not passed through as raw records.
- `--environment-input` accepts an explicit platform manifest (or a wrapper with `manifest`). Keep `agent.platform` consistent with `--platform`. The manifest may contain `agent`, `model`, `mcpServers`, `skills`, `plugins`, `instructions`, and `runtime`; unsupported top-level fields are omitted. Use it for a curated subset, known historical setup, or host versions/tool versions available in the task.

## Converter

Run `python scripts/capture.py --help` from this skill's directory. Python 3.11+ is required; no third-party package is needed. Output files contain redacted data; raw inputs stay untouched. Choose a fresh output directory outside source control. The converter refuses to overwrite outputs.

```bash
# Only the Session: configuration is neither required nor read.
python scripts/capture.py --mode session --platform codex --session /path/to/selected-rollout.jsonl --output /path/to/capture --title "Debugging the importer"

# Only environment; explicitly selected config layers.
python scripts/capture.py --mode environment --platform codex --config /path/to/config.toml --config /path/to/project-config.toml --output /path/to/environment

# Both, with Claude Code inputs.
python scripts/capture.py --mode both --platform claude-code --config /path/to/settings.json --config /path/to/.mcp.json --session /path/to/selected-session.jsonl --output /path/to/run

# Selected user turns, without tool records, as Markdown.
python scripts/capture.py --mode session --platform claude-code --session /path/to/selected-session.jsonl --turn-start 2 --turn-end 5 --messages-only --format markdown --output /path/to/selection

# Environment subset from a curated manifest.
python scripts/capture.py --mode environment --platform codex --environment-input /path/to/manifest.json --environment-fields agent,model,mcpServers --output /path/to/setup
```

Additional options:

- `--from` / `--to`: inclusive ISO timestamps. Filtering fails if any normalized event lacks a timestamp; it does not silently drop undated events.
- `--turn-start` / `--turn-end`: inclusive, one-based visible user-message turns; tool-result blocks do not start turns. Time and turn filters can be combined.
- `--skill-dir`: repeatable, explicitly selected directory whose immediate child skill folders are inventoried by name only; instructions/assets/scripts are not copied.
- `--profile`: select a Codex profile; unknown profiles fail. Runtime overrides remain unverified.
- `--model-id`, `--platform-version`, `--name`, `--title`: supply known metadata. A Session model override conflicting with recorded models fails. Multiple observed models are recorded in metadata and no single Session model is invented.
- `--started-at` / `--ended-at`: explicitly known Session start/completion timestamps. The first/last observed event times are kept in metadata and are not inferred as the Session's lifetime. Omit `--ended-at` for an active Session.
- `--environment-fields`: comma-separated top-level fields; `agent`, `schemaVersion`, and capture provenance are retained. Missing selected fields are not fabricated.
- `--redact-file`: explicitly selected UTF-8 file containing one exact sensitive value per line, applied to all output strings. Never pass literal credentials on the command line. Pattern redaction also masks common credentials, environment values, home-directory usernames, email addresses, and private-network URLs. Review residual confidential data before upload.

Outputs depend on scope:

| File | Purpose |
| --- | --- |
| `environment.json` | Redacted platform manifest; also usable as a website environment import |
| `environment-request.json` | `create_case_environment` fields except `caseSlug` |
| `transcript.jsonl` or `transcript.md` | Selected, converted transcript |
| `session-request.json` | `upload_case_session` fields except `caseSlug` and optional `environmentId` |
| `capture-report.json` | Scope, counts, omissions, redaction count, hashes, and upload-size eligibility |

Automatic config capture intentionally omits MCP command arguments, header values, and environment values because they often contain credentials. Executable names and required variable names remain when known. Add reviewed non-sensitive setup details through a curated manifest if necessary. The converter does not create summaries or upload anything; the Agent performs those requested steps using authorized content and the connected MCP tools.

## Format references

- [Codex configuration reference](https://developers.openai.com/codex/config-reference)
- [Codex rollout protocol source](https://github.com/openai/codex/blob/main/codex-rs/protocol/src/protocol.rs) and [response item source](https://github.com/openai/codex/blob/main/codex-rs/protocol/src/models.rs)
- [Claude Code directory and transcript locations](https://code.claude.com/docs/en/claude-directory)

These are source-format references, not a promise that every host version emits the same logs. Unsupported or omitted visible blocks are counted in the report and must be disclosed.
