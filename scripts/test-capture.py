"""Behavior checks with synthetic materials; never reads a user's real logs."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "plugins/agent-case-share-skills/skills/capture-agent-case-share/scripts/capture.py"
SPEC = importlib.util.spec_from_file_location("capture", SCRIPT)
capture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def source(self, name, content):
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return str(path)

    def jsonl(self, rows):
        return self.source("source.jsonl", "".join(json.dumps(row) + "\n" for row in rows))

    def run_capture(self, *options):
        args = capture.parser().parse_args(["--output", str(self.root / "output"), *options])
        report = capture.run(args)
        outputs = {path.name: path.read_text(encoding="utf-8") for path in (self.root / "output").iterdir()}
        return report, outputs

    def test_session_only_does_not_read_config(self):
        log = self.jsonl([{"role": "user", "content": "Hello"}])
        _, files = self.run_capture("--mode", "session", "--platform", "generic", "--session", log)
        self.assertNotIn("environment.json", files)
        request = json.loads(files["session-request.json"])
        self.assertNotIn("environmentId", request)
        self.assertNotIn("endedAt", request)
        self.assertNotIn("startedAt", request)

    def test_opposite_scope_is_rejected_before_any_read(self):
        for options in [
            ["--mode", "session", "--platform", "codex", "--config", "missing-secret.toml", "--session", "missing.jsonl"],
            ["--mode", "environment", "--platform", "codex", "--config", "missing.toml", "--session", "missing-secret.jsonl"],
        ]:
            with self.assertRaisesRegex(ValueError, "only mode"):
                self.run_capture(*options)
        self.assertFalse((self.root / "output").exists())

    def test_environment_whitelist_and_profile(self):
        config = self.source("config.toml", '''model = "default-model"
[profiles.review]
model = "review-model"
[mcp_servers.demo]
command = "node"
args = ["--secret", "DO_NOT_UPLOAD"]
bearer_token_env_var = "DEMO_KEY"
http_headers = { Authorization = "DO_NOT_UPLOAD" }
env = { DEMO_KEY = "DO_NOT_UPLOAD" }
''')
        _, files = self.run_capture("--mode", "environment", "--platform", "codex", "--config", config, "--profile", "review")
        env = json.loads(files["environment.json"])
        self.assertEqual(env["model"]["modelId"], "review-model")
        self.assertEqual(env["mcpServers"][0]["requiredVariableNames"], ["DEMO_KEY"])
        self.assertEqual(env["mcpServers"][0]["bearer_token_env_var"], "DEMO_KEY")
        self.assertNotIn("DO_NOT_UPLOAD", "".join(files.values()))
        self.assertNotIn("session-request.json", files)
        self.assertFalse(env["capture"]["historicalEnvironmentVerified"])

    def test_codex_messages_are_not_duplicated_and_reasoning_is_omitted(self):
        rows = [
            {"type": "turn_context", "payload": {"model": "test-model"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": "Task"}},
            {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Task"}]}},
            {"type": "response_item", "payload": {"type": "reasoning", "encrypted_content": "NEVER_EXPORT"}},
            {"type": "response_item", "payload": {"type": "message", "role": "assistant", "channel": "analysis", "content": [{"type": "output_text", "text": "NEVER_EXPORT"}]}},
            {"type": "response_item", "payload": {"type": "function_call", "name": "shell", "call_id": "call1", "arguments": '{"command":"test"}'}},
            {"type": "response_item", "payload": {"type": "function_call_output", "call_id": "call1", "output": "success"}},
            {"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Done"}]}},
            {"type": "event_msg", "payload": {"type": "agent_message", "message": "Done"}},
        ]
        _, files = self.run_capture("--mode", "session", "--platform", "codex", "--session", self.jsonl(rows))
        events = [json.loads(line) for line in files["transcript.jsonl"].splitlines()]
        self.assertEqual([event["role"] for event in events], ["user", "tool", "tool", "assistant"])
        self.assertNotIn("NEVER_EXPORT", "".join(files.values()))
        self.assertEqual(json.loads(files["session-request.json"])["modelId"], "test-model")

    def test_claude_tool_results_do_not_start_turns(self):
        rows = [
            {"type": "user", "uuid": "u1", "message": {"content": "First"}},
            {"type": "assistant", "uuid": "a1", "message": {"model": "claude-test", "content": [{"type": "thinking", "thinking": "NEVER_EXPORT"}, {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file": "a.txt"}}]}},
            {"type": "user", "uuid": "r1", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "result"}]}},
            {"type": "assistant", "uuid": "a2", "message": {"content": [{"type": "text", "text": "First done"}]}},
            {"type": "user", "uuid": "u2", "message": {"content": [{"type": "text", "text": "Second"}]}},
            {"type": "user", "uuid": "u2", "message": {"content": "Second"}},
            {"type": "assistant", "uuid": "a3", "isSidechain": True, "message": {"content": "NEVER_EXPORT"}},
            {"type": "assistant", "uuid": "a4", "message": {"content": "Second done"}},
        ]
        _, files = self.run_capture("--mode", "session", "--platform", "claude-code", "--session", self.jsonl(rows), "--turn-start", "2", "--turn-end", "2", "--messages-only")
        events = [json.loads(line) for line in files["transcript.jsonl"].splitlines()]
        self.assertEqual([event["content"] for event in events], ["Second", "Second done"])
        self.assertTrue(all(event["turn"] == 2 for event in events))
        self.assertNotIn("NEVER_EXPORT", "".join(files.values()))

    def test_both_mode_and_environment_subset(self):
        manifest = self.source("env.json", json.dumps({"agent": {"platform": "codex"}, "model": {"modelId": "x"}, "skills": [{"name": "demo"}], "unknown": "NEVER_EXPORT"}))
        log = self.jsonl([{"role": "user", "content": "task"}])
        _, files = self.run_capture("--mode", "both", "--platform", "codex", "--environment-input", manifest, "--environment-fields", "agent,skills", "--session", log)
        self.assertNotIn("model", json.loads(files["environment.json"]))
        self.assertIn("session-request.json", files)
        self.assertNotIn("environmentId", json.loads(files["session-request.json"]))
        self.assertNotIn("NEVER_EXPORT", "".join(files.values()))

    def test_time_selection_and_missing_timestamps(self):
        log = self.jsonl([
            {"role": "user", "content": "before", "timestamp": "2026-09-27T00:00:00Z"},
            {"role": "assistant", "content": "inside", "timestamp": "2026-09-27T08:00:00.500+08:00"},
        ])
        _, files = self.run_capture("--mode", "session", "--platform", "generic", "--session", log, "--from", "2026-09-27T00:00:00Z", "--to", "2026-09-27T00:00:00.750Z")
        events = [json.loads(line) for line in files["transcript.jsonl"].splitlines()]
        self.assertEqual(len(events), 2)

    def test_time_filter_requires_dated_events(self):
        log = self.jsonl([{"role": "user", "content": "undated"}])
        with self.assertRaisesRegex(ValueError, "timestamps"):
            self.run_capture("--mode", "session", "--platform", "generic", "--session", log, "--from", "2026-09-27T00:00:00Z")

    def test_tool_output_omits_media_and_encrypted_content(self):
        rows = [{"type": "response_item", "payload": {"type": "function_call_output", "call_id": "x", "output": [
            {"type": "input_text", "text": "Result"},
            {"type": "encrypted_content", "encrypted_content": "NEVER_EXPORT"},
            {"type": "input_image", "image_url": "data:image/png;base64,NEVER_EXPORT"},
        ]}}]
        report, files = self.run_capture("--mode", "session", "--platform", "codex", "--session", self.jsonl(rows))
        self.assertNotIn("NEVER_EXPORT", "".join(files.values()))
        self.assertEqual(json.loads(files["transcript.jsonl"])["output"], "Result")
        self.assertEqual(report["session"]["omittedBlocks"], 2)

    def test_model_conflict_and_reversed_filters_fail_without_outputs(self):
        log = self.jsonl([{"type": "turn_context", "payload": {"model": "recorded"}}, {"role": "user", "content": "task"}])
        with self.assertRaisesRegex(ValueError, "conflicts"):
            self.run_capture("--mode", "session", "--platform", "codex", "--session", log, "--model-id", "different")
        with self.assertRaisesRegex(ValueError, "reversed"):
            self.run_capture("--mode", "session", "--platform", "codex", "--session", log, "--turn-start", "3", "--turn-end", "1")
        self.assertFalse((self.root / "output").exists())

    def test_unicode_limit_uses_mcp_character_count(self):
        source = self.source("unicode.md", "😀" * 500_001)
        report, files = self.run_capture("--mode", "session", "--platform", "generic", "--session", source)
        self.assertFalse(report["session"]["withinMcpLimit"])
        self.assertEqual(report["session"]["transcriptCharacters"], 1_000_002)
        self.assertEqual(len(files["transcript.md"]), 500_001)

    def test_observed_times_are_distinct_from_session_lifetime(self):
        log = self.jsonl([{"role": "user", "content": "Task", "timestamp": "2026-09-27T00:01:00Z"}])
        _, files = self.run_capture("--mode", "session", "--platform", "generic", "--session", log,
                                    "--started-at", "2026-09-27T00:00:00Z", "--ended-at", "2026-09-27T00:02:00Z")
        request = json.loads(files["session-request.json"])
        self.assertEqual(request["startedAt"], "2026-09-27T00:00:00.000000Z")
        self.assertEqual(request["endedAt"], "2026-09-27T00:02:00.000000Z")
        self.assertEqual(request["metadata"]["firstObservedAt"], "2026-09-27T00:01:00.000000Z")

    def test_redaction_in_messages_tools_and_manifest(self):
        redactor = capture.Redactor(["CUSTOM_SECRET"])
        output = redactor.data({"env": {"NORMAL_NAME": "HIDDEN_VALUE"}, "password": "HIDDEN_VALUE", "content": 'token="HIDDEN_VALUE"\nNORMAL_NAME=HIDDEN_VALUE\nhttps://127.0.0.1/path https://public.example/path?opaque=HIDDEN_VALUE\nuser@example.com CUSTOM_SECRET sk-proj-abcdefghijklmnop'})
        encoded = json.dumps(output)
        for value in ("HIDDEN_VALUE", "CUSTOM_SECRET", "user@example.com", "sk-proj-abcdefghijklmnop", "127.0.0.1"):
            self.assertNotIn(value, encoded)
        self.assertIn("NORMAL_NAME", encoded)
        self.assertIn("https://public.example/path", encoded)

    def test_markdown_export_and_refusal_of_false_filtering(self):
        source = self.source("session.md", "# User\n\nHello\n")
        _, files = self.run_capture("--mode", "session", "--platform", "generic", "--session", source)
        self.assertEqual(files["transcript.md"], "# User\n\nHello\n")
        with self.assertRaisesRegex(ValueError, "Markdown cannot"):
            capture.session(capture.parser().parse_args(["--mode", "session", "--platform", "generic", "--session", source, "--messages-only", "--output", "unused"]), capture.Redactor())

    def test_oversized_export_is_preserved_and_reported(self):
        source = self.source("large.md", "a" * 1_000_001)
        report, files = self.run_capture("--mode", "session", "--platform", "generic", "--session", source)
        self.assertFalse(report["session"]["withinMcpLimit"])
        self.assertEqual(len(files["transcript.md"]), 1_000_001)

    def test_malformed_log_and_existing_output_do_not_overwrite(self):
        source = self.source("bad.jsonl", '{"role":"user"}\nNOT_JSON_SECRET\n')
        with self.assertRaisesRegex(ValueError, "line 2"):
            self.run_capture("--mode", "session", "--platform", "generic", "--session", source)
        self.assertFalse((self.root / "output").exists())
        source = self.source("good.md", "Original")
        self.run_capture("--mode", "session", "--platform", "generic", "--session", source)
        with self.assertRaisesRegex(ValueError, "overwritten"):
            self.run_capture("--mode", "session", "--platform", "generic", "--session", source)
        self.assertEqual((self.root / "output/transcript.md").read_text(), "Original")


if __name__ == "__main__":
    unittest.main()
