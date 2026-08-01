---
name: configure-agent-case-share
description: Configure the local Agent Case Share MCP credentials for Codex, Claude, Gemini, and other desktop agents. Use when the user asks to set up, connect, change, check, or clear the local connection.
---

# Configure Agent Case Share

Use this skill to configure the current user's local Agent Case Share credentials.

## Safety

- Do not ask the user to paste an API key into chat.
- Do not print, log, commit, or include the API key in generated files.
- This configuration skill makes no Agent Case Share network request. It only stores the local credential and configures the local client-side authentication reference.
- Run the bundled `scripts/configure.mjs` script from this skill directory. It prompts for the key without echoing it and stores it outside the workspace.
- On Windows, the script also stores the key as a user-scoped `AGENT_CASE_SHARE_API_KEY` environment variable through PowerShell stdin. The key is never passed as a command-line argument or written to Codex `config.toml`.
- The script stores configuration in a user-only location:
  - Windows: `%APPDATA%\\agent-case-share\\config.json`
  - macOS: `~/Library/Application Support/agent-case-share/config.json`
  - Linux: `$XDG_CONFIG_HOME/agent-case-share/config.json`, or `~/.config/agent-case-share/config.json`

## Workflow

1. Locate this skill's `scripts/configure.mjs` file and ask the user to run it in a local terminal:
   ```bash
   node /absolute/path/to/configure-agent-case-share/scripts/configure.mjs
   ```
2. The script securely prompts for the personal key created in the user's Agent Case Share profile, saves it outside the workspace, and, when a Codex configuration is detected, registers the remote MCP server idempotently with a bearer-token environment reference:
   ```toml
   [mcp_servers.agent-case-share]
   url = "https://mcp.agentcaseshare.cn/mcp"
   bearer_token_env_var = "AGENT_CASE_SHARE_API_KEY"
   ```
   It does not replace or rewrite unrelated MCP entries. Use `--no-mcp` to save only the credential.
3. Restart Codex after setup so it inherits the user-scoped environment variable and reloads MCP tools.
4. To verify setup without exposing the key, run:
   ```bash
   node /absolute/path/to/configure-agent-case-share/scripts/configure.mjs --status
   ```
5. To intentionally delete the saved credential and user-scoped bearer variable, run:
   ```bash
   node /absolute/path/to/configure-agent-case-share/scripts/configure.mjs --clear
   ```
6. Confirm only that configuration succeeded. Never repeat the key.

## Credential Resolution

The local CLI and compatibility integrations read the configuration file written by this skill. Codex Streamable HTTP MCP reads the bearer token from the user-scoped `AGENT_CASE_SHARE_API_KEY` environment variable configured by the script. After setup, do not copy the personal API key into an MCP client JSON/TOML file or pass it as a tool argument.

Other Agent Case Share skills resolve settings in this order:

1. The user configuration file written by this skill.
2. `AGENT_CASE_SHARE_API_KEY` and optional `AGENT_CASE_SHARE_BASE_URL` environment variables for MCP, CLI, CI, or Gemini extension compatibility.
3. The default base URL `https://agentcaseshare.cn/` for unauthenticated public reads.

If the connected MCP server reports missing credentials, invoke this skill. Do not request the key in conversation.
