---
name: configure-agent-case-share
description: Configure the local Agent Case Share account for Codex, Claude, Gemini, and other desktop agents. Use when the user asks to set up, connect, sign in, change, check, or clear Agent Case Share API credentials.
---

# Configure Agent Case Share

Use this skill to configure the current user's local Agent Case Share credentials.

## Safety

- Do not ask the user to paste an API key into chat.
- Do not print, log, commit, or include the API key in generated files.
- This configuration skill makes no Agent Case Share HTTP request. If it is extended to do so, explicitly set `User-Agent: AgentCaseShare-AIClient/1.0` and `Accept: application/json`; add `Content-Type: application/json` for JSON requests, never rely on Python `urllib`, curl, Node `fetch`, or another default User-Agent, and never impersonate a browser.
- Run the bundled `scripts/configure.mjs` script from this skill directory. It prompts for the key without echoing it and stores it outside the workspace.
- The script stores configuration in a user-only location:
  - Windows: `%APPDATA%\\agent-case-share\\config.json`
  - macOS: `~/Library/Application Support/agent-case-share/config.json`
  - Linux: `$XDG_CONFIG_HOME/agent-case-share/config.json`, or `~/.config/agent-case-share/config.json`

## Workflow

1. Locate this skill's `scripts/configure.mjs` file and ask the user to run it in a local terminal:
   ```bash
   node /absolute/path/to/configure-agent-case-share/scripts/configure.mjs
   ```
2. The script securely prompts for the personal API key from the Agent Case Share `/profile` page and saves the default base URL `https://agentcaseshare.cn/` automatically.
3. To verify setup without exposing the key, run:
   ```bash
   node /absolute/path/to/configure-agent-case-share/scripts/configure.mjs --status
   ```
4. To intentionally delete the saved configuration, run:
   ```bash
   node /absolute/path/to/configure-agent-case-share/scripts/configure.mjs --clear
   ```
5. Confirm only that configuration succeeded. Never repeat the key.

## Credential Resolution

Other Agent Case Share skills resolve settings in this order:

1. The user configuration file written by this skill.
2. `AGENT_CASE_SHARE_API_KEY` and optional `AGENT_CASE_SHARE_BASE_URL` environment variables for CLI, CI, or Gemini extension compatibility.
3. The default base URL `https://agentcaseshare.cn/` for unauthenticated public reads.

If authentication is required and neither the user configuration file nor an environment variable provides a key, invoke this skill. Do not request the key in conversation as a fallback.
