#!/usr/bin/env python3
"""Convert explicitly selected run materials locally. No network or implicit reads."""

import argparse
import hashlib
import ipaddress
import json
import platform as host_platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from urllib.parse import urlsplit

SCHEMA = "agent-environment/v1"
ENV_FIELDS = {"agent", "model", "mcpServers", "skills", "plugins", "runtime", "instructions"}
SENSITIVE_KEY = re.compile(
    r"(?i)(api.?key|token|secret|password|passwd|authorization|cookie|private.?key|credential)"
)


class CaptureError(ValueError):
    """An error whose message contains only safe, authored guidance."""


def iso_time(value):
    if not isinstance(value, str):
        raise CaptureError("Timestamps must be ISO strings with a timezone.")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise CaptureError("Timestamps must include a timezone.")
    return stamp.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def object_file(path):
    content = Path(path).read_text(encoding="utf-8-sig")
    if Path(path).suffix.lower() == ".toml":
        import tomllib
        value = tomllib.loads(content)
    else:
        value = json.loads(content)
    if not isinstance(value, dict):
        raise CaptureError("Configuration and manifests must be JSON/TOML objects.")
    return value


def merge(left, right):
    result = dict(left)
    for key, value in right.items():
        result[key] = merge(result[key], value) if isinstance(result.get(key), dict) and isinstance(value, dict) else value
    return result


def basename(value):
    return PureWindowsPath(value).name if "\\" in value else Path(value).name


class Redactor:
    def __init__(self, values=()):
        self.values = sorted(set(values), key=len, reverse=True)
        self.count = 0

    def replace(self, pattern, text, replacement="[REDACTED]", flags=0):
        text, count = re.subn(pattern, replacement, text, flags=flags)
        self.count += count
        return text

    def text(self, text):
        for value in self.values:
            count = text.count(value)
            if count:
                text = text.replace(value, "[REDACTED]")
                self.count += count
        text = self.replace(r"-----BEGIN [^-\n]*PRIVATE KEY-----[\s\S]*?-----END [^-\n]*PRIVATE KEY-----", text)
        text = self.replace(r"\b(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{12,}|acsp_live_[A-Za-z0-9_-]+|gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]+|AKIA[A-Z0-9]{16})\b", text)
        text = self.replace(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b", text)
        text = self.replace(r"(?i)\bBearer\s+[^\s\"',;]+", text, "Bearer [REDACTED]")
        text = self.replace(
            r'''(?ix)(?<![\w-])(["']?(?:[\w-]{0,64}(?:api[_-]?key|token|secret|password|passwd|authorization|cookie|credential)[\w-]{0,64})["']?\s*[:=]\s*)(?:"[^"\n]*"|'[^'\n]*'|[^\s,;\}\]\n]+)''',
            text, lambda match: match.group(1) + '"[REDACTED]"',
        )
        text = self.replace(r"(?im)^(\s*(?:export\s+)?[A-Z][A-Z0-9_]*\s*=).*$", text, lambda match: match.group(1) + "[REDACTED]")
        text = self.replace(r'''(?i)(--(?:api-key|token|secret|password|credential)\s+)(?:"[^"\n]*"|'[^'\n]*'|[^\s,;]+)''', text, lambda match: match.group(1) + "[REDACTED]")
        text = self.replace(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]{1,128}@[A-Za-z0-9.-]{1,255}\.[A-Za-z]{2,}", text)
        text = self.replace(r"(?i)([A-Z]:[\\/]Users[\\/])[^\\/\s\"']+", text, lambda match: match.group(1) + "[USER]")
        text = self.replace(r"(/(?:home|Users)/)[^/\s\"']+", text, lambda match: match.group(1) + "[USER]")

        def clean_url(match):
            value = match.group(0)
            try:
                url = urlsplit(value)
                host = url.hostname or ""
                private = host.lower() in {"localhost", "localhost.localdomain"} or host.lower().endswith((".local", ".internal", ".lan"))
                try:
                    private = private or not ipaddress.ip_address(host).is_global
                except ValueError:
                    pass
                if private:
                    self.count += 1
                    return "[REDACTED_ENDPOINT]"
                # Userinfo, query strings and fragments can contain opaque credentials.
                if url.username is not None or url.query or url.fragment:
                    self.count += 1
                    authority = url.netloc.rsplit("@", 1)[-1]
                    return f"{url.scheme}://{authority}{url.path}"
            except ValueError:
                self.count += 1
                return "[REDACTED_ENDPOINT]"
            return value

        return re.sub(r"https?://[^\s<>\"']+", clean_url, text)

    def data(self, value, key=""):
        # Keep variable *names*, never their values.
        if key.lower() in {"env", "environmentvariables", "environment_variables", "headers", "http_headers"} and isinstance(value, dict):
            self.count += len(value)
            return {self.text(str(name)): "[REDACTED]" for name in value}
        if key not in {"environmentId", "schemaVersion", "bearer_token_env_var"} and SENSITIVE_KEY.search(key):
            self.count += 1
            return "[REDACTED]"
        if isinstance(value, dict):
            return {self.text(str(name)): self.data(item, str(name)) for name, item in value.items()}
        if isinstance(value, list):
            return [self.data(item) for item in value]
        if isinstance(value, str):
            return self.text(value)
        return value


def environment(args):
    if args.environment_input:
        supplied = object_file(args.environment_input)
        manifest = supplied.get("manifest", supplied)
        if not isinstance(manifest, dict):
            raise CaptureError("manifest must be an object.")
        if manifest.get("schemaVersion", SCHEMA) != SCHEMA:
            raise CaptureError("Unsupported environment schemaVersion.")
        manifest = {key: value for key, value in manifest.items() if key in ENV_FIELDS}
        provenance = "supplied_manifest"
    else:
        config = {}
        for path in args.config:
            config = merge(config, object_file(path))
        if args.profile:
            profile = config.get("profiles", {}).get(args.profile)
            if not isinstance(profile, dict):
                raise CaptureError("Selected profile was not found in the supplied configuration.")
            config = merge(config, profile)
        manifest = {"agent": {"platform": args.platform}}
        model_id = config.get("model")
        if isinstance(model_id, str) and model_id:
            manifest["model"] = {"modelId": model_id}
            if isinstance(config.get("model_provider"), str):
                manifest["model"]["provider"] = config["model_provider"]
            if isinstance(config.get("model_reasoning_effort"), str):
                manifest["model"]["reasoningEffort"] = config["model_reasoning_effort"]
        servers = config.get("mcp_servers", config.get("mcpServers", {}))
        if isinstance(servers, dict):
            manifest["mcpServers"] = []
            for name, entry in servers.items():
                if not isinstance(entry, dict):
                    continue
                server = {"name": name, "captureState": "configured"}
                for key in ("url", "enabled", "type", "bearer_token_env_var"):
                    if key in entry:
                        server[key] = entry[key]
                if isinstance(entry.get("command"), str):
                    server["command"] = basename(entry["command"])
                if isinstance(entry.get("env"), dict):
                    server["requiredVariableNames"] = sorted(entry["env"])
                server["setupNotes"] = "Command arguments, environment values and headers omitted."
                manifest["mcpServers"].append(server)
        skills = config.get("skills", {})
        if isinstance(skills, dict) and isinstance(skills.get("config"), list):
            manifest["skills"] = [{"name": basename(entry["path"]), "enabled": entry.get("enabled", True), "captureState": "configured_override"}
                                  for entry in skills["config"] if isinstance(entry, dict) and isinstance(entry.get("path"), str)]
        plugins = config.get("enabledPlugins", config.get("plugins", {}))
        if isinstance(plugins, dict):
            manifest["plugins"] = [{"name": name, "enabled": entry.get("enabled", True) if isinstance(entry, dict) else entry,
                                    "captureState": "configured"} for name, entry in plugins.items()]
        manifest["runtime"] = {"os": host_platform.system().lower(), "architecture": host_platform.machine(), "captureHost": True}
        provenance = "current_supplied_configuration"
    agent = manifest.setdefault("agent", {})
    if not isinstance(agent, dict) or agent.get("platform", args.platform).lower() != args.platform:
        raise CaptureError("Environment platform conflicts with the selected platform.")
    agent["platform"] = args.platform
    if args.platform_version:
        agent["version"] = args.platform_version
    if args.model_id:
        existing = manifest.get("model", {}).get("modelId")
        if existing and existing != args.model_id:
            raise CaptureError("Environment model conflicts with the supplied model ID.")
        manifest.setdefault("model", {})["modelId"] = args.model_id
    for directory in args.skill_dir:
        root = Path(directory)
        if not root.is_dir():
            raise CaptureError("Selected skill directory does not exist.")
        inventory = [root] if (root / "SKILL.md").is_file() else sorted(root.iterdir())
        manifest.setdefault("skills", []).extend({"name": child.name, "captureState": "installed"}
                                                  for child in inventory if (child / "SKILL.md").is_file())
    selected = set(args.environment_fields.split(",")) if args.environment_fields else ENV_FIELDS
    if selected - ENV_FIELDS:
        raise CaptureError("Unknown environment field selection.")
    manifest = {key: value for key, value in manifest.items() if key in selected or key == "agent"}
    manifest["schemaVersion"] = SCHEMA
    manifest["capture"] = {"provenance": provenance, "capturedAt": datetime.now(timezone.utc).isoformat(),
                           "historicalEnvironmentVerified": False, "configurationLayerCount": len(args.config),
                           "limitations": "Only explicitly supplied sources; runtime overrides and actual integration use are not inferred."}
    return manifest


def records(path):
    result = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            raise CaptureError(f"Invalid JSONL at line {number}; no raw content was printed.") from None
        if not isinstance(row, dict):
            raise CaptureError(f"JSONL line {number} must be an object.")
        result.append(row)
    return result


def normalize(rows, platform):
    events, models, seen = [], set(), set()
    stats = {"omittedBlocks": 0, "duplicateRecords": 0, "sourceRecords": len(rows)}
    response_roles = {row.get("payload", {}).get("role") for row in rows
                      if row.get("type") == "response_item" and isinstance(row.get("payload"), dict) and row["payload"].get("type") == "message" and row["payload"].get("channel") != "analysis"}

    def add(role, content=None, stamp=None, **extra):
        event = {"role": role}
        if content is not None:
            event["content"] = content
        if stamp:
            event["createdAt"] = iso_time(stamp)
        event.update(extra)
        events.append(event)

    def output_text(value):
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts = [block["text"] for block in value if isinstance(block, dict) and block.get("type") in {"text", "input_text", "output_text"} and isinstance(block.get("text"), str)]
            stats["omittedBlocks"] += len(value) - len(parts)
            return "\n".join(parts)
        stats["omittedBlocks"] += 1
        return "[Unsupported output omitted]"

    def blocks(role, content, stamp):
        if isinstance(content, str):
            if content:
                add(role, content, stamp)
                return True
            return False
        if not isinstance(content, list):
            stats["omittedBlocks"] += 1
            return False
        # Contiguous text blocks in one message form one visible user turn.
        text_parts = []
        user_text = False

        def flush():
            nonlocal user_text
            if text_parts:
                add(role, "\n".join(text_parts), stamp)
                user_text = user_text or role == "user"
                text_parts.clear()

        for block in content:
            if not isinstance(block, dict):
                stats["omittedBlocks"] += 1
                continue
            kind = block.get("type")
            if kind in {"text", "input_text", "output_text"} and isinstance(block.get("text"), str):
                text_parts.append(block["text"])
            else:
                flush()
                if kind == "tool_use":
                    add("tool", stamp=stamp, toolName=block.get("name", "unknown"), callId=block.get("id", ""), arguments=block.get("input", {}))
                elif kind == "tool_result":
                    output = output_text(block.get("content", ""))
                    add("tool", stamp=stamp, callId=block.get("tool_use_id", ""), output=output)
                else:
                    stats["omittedBlocks"] += 1
        flush()
        return user_text

    turn = 0
    for row in rows:
        offset = len(events)
        stamp = row.get("createdAt", row.get("timestamp"))
        new_turn = False
        if platform == "codex" and row.get("type") in {"response_item", "event_msg", "turn_context", "session_meta", "compacted"}:
            payload = row.get("payload", {})
            if not isinstance(payload, dict):
                raise CaptureError("Codex payload must be an object.")
            kind = payload.get("type")
            if row["type"] == "turn_context":
                if isinstance(payload.get("model"), str):
                    models.add(payload["model"])
            elif row["type"] == "response_item":
                if kind == "message" and payload.get("role") in {"user", "assistant"}:
                    role = payload["role"]
                    if payload.get("channel") == "analysis":
                        stats["omittedBlocks"] += 1
                    else:
                        new_turn = blocks(role, payload.get("content"), stamp) and role == "user"
                elif kind in {"function_call", "custom_tool_call"}:
                    add("tool", stamp=stamp, toolName=payload.get("name", "unknown"), callId=payload.get("call_id", ""),
                        arguments=payload.get("arguments", payload.get("input", "")))
                elif kind in {"function_call_output", "custom_tool_call_output"}:
                    add("tool", stamp=stamp, callId=payload.get("call_id", ""), output=output_text(payload.get("output", "")))
                else:
                    stats["omittedBlocks"] += 1
            elif row["type"] == "event_msg" and kind in {"user_message", "agent_message"}:
                role = "user" if kind == "user_message" else "assistant"
                if role in response_roles:
                    stats["duplicateRecords"] += 1
                else:
                    new_turn = blocks(role, payload.get("message", ""), stamp) and role == "user"
        elif platform == "claude-code" and row.get("type") in {"user", "assistant"}:
            if row.get("isSidechain"):
                stats["omittedBlocks"] += 1
                continue
            identity = row.get("uuid")
            if identity and identity in seen:
                stats["duplicateRecords"] += 1
                continue
            if identity:
                seen.add(identity)
            message = row.get("message", {})
            if not isinstance(message, dict):
                raise CaptureError("Claude Code message must be an object.")
            if isinstance(message.get("model"), str):
                models.add(message["model"])
            role = row["type"]
            new_turn = blocks(role, message.get("content"), stamp) and role == "user"
        elif row.get("role") in {"user", "assistant", "tool"}:
            role = row["role"]
            if role == "tool":
                extra = {key: row[key] for key in ("toolName", "callId", "arguments", "output") if key in row}
                if "output" in extra:
                    extra["output"] = output_text(extra["output"])
                add(role, output_text(row["content"]) if "content" in row else None, stamp, **extra)
            else:
                new_turn = blocks(role, row.get("content"), stamp) and role == "user"
        else:
            stats["omittedBlocks"] += 1
        if new_turn:
            turn += 1
        for event in events[offset:]:
            event["turn"] = turn
    return events, sorted(models), stats


def render_markdown(events):
    sections = ["# Converted Session transcript"]
    for event in events:
        title = event["role"].capitalize()
        if event.get("toolName"):
            title += ": " + event["toolName"]
        if event.get("createdAt"):
            title += " (" + event["createdAt"] + ")"
        content = event.get("content", "")
        for key in ("arguments", "output"):
            if key in event:
                value = event[key] if isinstance(event[key], str) else json.dumps(event[key], ensure_ascii=False, indent=2)
                content += f"\n\n{key.capitalize()}:\n\n{value}"
        sections.append(f"## {title}\n\n{content}")
    return "\n\n".join(sections) + "\n"


def session(args, redactor):
    markdown = Path(args.session).suffix.lower() in {".md", ".markdown", ".txt"}
    filters = {"messagesOnly": args.messages_only, "from": args.from_time, "to": args.to_time,
               "turnStart": args.turn_start, "turnEnd": args.turn_end}
    metadata = {"captureKind": "converted_transcript", "scope": filters,
                "completeRawBackup": False, "sourcePlatform": args.platform}
    request = {"title": args.title or "Captured Session", "platform": args.platform, "metadata": metadata}
    if markdown:
        if args.messages_only or args.from_time or args.to_time or args.turn_start or args.turn_end:
            raise CaptureError("Markdown cannot be filtered by messages, time, or turns; provide structured JSONL or a preselected export.")
        transcript = redactor.text(Path(args.session).read_text(encoding="utf-8-sig"))
        format_name = "markdown"
        metadata["captureKind"] = "supplied_markdown"
        stats = {"sourceRecords": None, "selectedEvents": None}
        if args.model_id:
            request["modelId"] = args.model_id
    else:
        events, models, stats = normalize(records(args.session), args.platform)
        start = iso_time(args.from_time) if args.from_time else None
        end = iso_time(args.to_time) if args.to_time else None
        if start or end:
            if any("createdAt" not in event for event in events):
                raise CaptureError("Time selection requires timestamps on all normalized events.")
            events = [event for event in events if (not start or event["createdAt"] >= start) and (not end or event["createdAt"] <= end)]
        if args.turn_start or args.turn_end:
            events = [event for event in events if (not args.turn_start or event["turn"] >= args.turn_start) and (not args.turn_end or event["turn"] <= args.turn_end)]
        if args.messages_only:
            events = [event for event in events if event["role"] != "tool"]
        if not events:
            raise CaptureError("No visible events match the selected source and scope.")
        if args.model_id and models and models != [args.model_id]:
            raise CaptureError("Session model override conflicts with recorded models.")
        if args.model_id or len(models) == 1:
            request["modelId"] = args.model_id or models[0]
        metadata["observedModels"] = models
        for sequence, event in enumerate(events, 1):
            event["sequence"] = sequence
        events = redactor.data(events)
        stats["selectedEvents"] = len(events)
        metadata.update(stats)
        metadata["partialSelection"] = bool(args.messages_only or start or end or args.turn_start or args.turn_end)
        if events[0].get("createdAt"):
            metadata["firstObservedAt"] = events[0]["createdAt"]
        if events[-1].get("createdAt"):
            metadata["lastObservedAt"] = events[-1]["createdAt"]
        format_name = args.format
        transcript = render_markdown(events) if format_name == "markdown" else "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events)
    if not transcript.strip():
        raise CaptureError("Transcript must not be empty.")
    request = redactor.data(request)
    if args.started_at:
        request["startedAt"] = args.started_at
    if args.ended_at:
        request["endedAt"] = args.ended_at
    request.update(transcriptFormat=format_name, transcript=transcript)
    return request, stats


def parser():
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("--mode", required=True, choices=("environment", "session", "both"))
    command.add_argument("--platform", required=True, help="codex, claude-code, or another host name for generic exports")
    command.add_argument("--output", required=True, help="Fresh local output directory; existing outputs are never overwritten")
    command.add_argument("--config", action="append", default=[], help="Explicit TOML/JSON config; repeat in precedence order")
    command.add_argument("--environment-input", help="Explicit JSON manifest instead of native config")
    command.add_argument("--environment-fields", help="Comma-separated manifest fields")
    command.add_argument("--skill-dir", action="append", default=[])
    command.add_argument("--profile")
    command.add_argument("--session", help="Exact selected transcript/log path")
    command.add_argument("--format", choices=("jsonl", "markdown"), default="jsonl")
    command.add_argument("--messages-only", action="store_true")
    command.add_argument("--from", dest="from_time")
    command.add_argument("--to", dest="to_time")
    command.add_argument("--turn-start", type=int)
    command.add_argument("--turn-end", type=int)
    command.add_argument("--title")
    command.add_argument("--name")
    command.add_argument("--model-id")
    command.add_argument("--platform-version")
    command.add_argument("--started-at", help="Known Session start time, not merely the first observed event")
    command.add_argument("--ended-at", help="Known completed Session end time; omit for an active Session")
    command.add_argument("--redact-file", help="Explicit local file of exact sensitive values, one per line")
    return command


def run(args):
    args.platform = args.platform.strip().lower()
    if not args.platform or len(args.platform) > 80:
        raise CaptureError("Platform must contain 1-80 characters.")
    for value, limit, label in ((args.name, 160, "name"), (args.title, 200, "title"), (args.model_id, 160, "model ID"), (args.platform_version, 160, "platform version")):
        if value is not None and (not value.strip() or len(value) > limit):
            raise CaptureError(f"Invalid {label}: use 1-{limit} characters.")
    capture_env, capture_session = args.mode != "session", args.mode != "environment"
    if not capture_env and (args.config or args.environment_input or args.skill_dir or args.profile or args.environment_fields or args.platform_version or args.name):
        raise CaptureError("Session-only mode does not accept environment sources/options.")
    if not capture_session and (args.session or args.messages_only or args.from_time or args.to_time or args.turn_start or args.turn_end or args.title or args.started_at or args.ended_at):
        raise CaptureError("Environment-only mode does not accept Session sources/options.")
    if capture_env and not (args.config or args.environment_input or args.skill_dir):
        raise CaptureError("Select an explicit configuration, environment manifest, or skill directory.")
    if args.environment_input and (args.config or args.profile):
        raise CaptureError("Choose a supplied manifest or native configuration, not both.")
    if args.profile and args.platform != "codex":
        raise CaptureError("Profile selection is supported for supplied Codex configuration only.")
    if capture_session and not args.session:
        raise CaptureError("Select an explicit Session source path.")
    if any(value is not None and value < 1 for value in (args.turn_start, args.turn_end)):
        raise CaptureError("Turn numbers start at one.")
    if args.turn_start and args.turn_end and args.turn_end < args.turn_start:
        raise CaptureError("Turn range is reversed.")
    if args.from_time:
        args.from_time = iso_time(args.from_time)
    if args.to_time:
        args.to_time = iso_time(args.to_time)
    if args.from_time and args.to_time and args.to_time < args.from_time:
        raise CaptureError("Time interval is reversed.")
    if args.started_at:
        args.started_at = iso_time(args.started_at)
    if args.ended_at:
        args.ended_at = iso_time(args.ended_at)
    if args.started_at and args.ended_at and args.ended_at < args.started_at:
        raise CaptureError("Known Session start/end times are reversed.")
    output = Path(args.output)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise CaptureError("Use a fresh or empty output directory; existing files will not be overwritten.")
    values = Path(args.redact_file).read_text(encoding="utf-8-sig").splitlines() if args.redact_file else []
    redactor = Redactor(value for value in values if value)
    files, report = {}, {"mode": args.mode, "platform": args.platform, "uploadPerformed": False}
    if capture_env:
        manifest = redactor.data(environment(args))
        env_request = {"name": redactor.text(args.name or "Captured environment"), "platform": args.platform,
                       "schemaVersion": SCHEMA, "manifest": manifest}
        if manifest["agent"].get("version"):
            env_request["platformVersion"] = manifest["agent"]["version"]
        if isinstance(manifest.get("model"), dict) and manifest["model"].get("modelId"):
            env_request["modelId"] = manifest["model"]["modelId"]
        files["environment.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        files["environment-request.json"] = json.dumps(env_request, ensure_ascii=False, indent=2) + "\n"
        report["environmentFields"] = sorted(manifest)
    if capture_session:
        request, stats = session(args, redactor)
        files["session-request.json"] = json.dumps(request, ensure_ascii=False, indent=2) + "\n"
        transcript = request["transcript"]
        files["transcript.md" if request["transcriptFormat"] == "markdown" else "transcript.jsonl"] = transcript
        characters = len(transcript.encode("utf-16-le")) // 2
        report["session"] = {**stats, "transcriptCharacters": characters, "withinMcpLimit": characters <= 1_000_000}
    report["redactionCount"] = redactor.count
    report["reviewRequired"] = "Check for task-specific confidential data and omissions before a requested upload."
    report["sha256"] = {name: hashlib.sha256(content.encode("utf-8")).hexdigest() for name, content in files.items()}
    files["capture-report.json"] = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    output.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        with (output / name).open("x", encoding="utf-8", newline="\n") as destination:
            destination.write(content)
    return report


def main():
    if sys.version_info < (3, 11):
        print("Capture requires Python 3.11 or newer.", file=sys.stderr)
        return 1
    try:
        report = run(parser().parse_args())
    except CaptureError as error:
        print(f"Capture failed: {error} No upload was performed.", file=sys.stderr)
        return 1
    except (ValueError, OSError, TypeError, KeyError, AttributeError):
        # Parser errors may embed sensitive raw configuration values or paths.
        # Deliberately print only a safe error for malformed source data.
        print("Capture failed: invalid scope, source format, metadata, or output path. Check --help and your selected inputs; no upload was performed.", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
