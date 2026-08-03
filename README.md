# Agent Case Share Skill

Reusable AI-agent skills for searching, reading, publishing, and editing Agent Case Share content, case attachments, and reusable assets through MCP.

## Install

### Codex

Add this repository as a marketplace:

```bash
codex plugin marketplace add parkerluxu/agent-case-share-skills
```

Then install `agent-case-share-skills` from the Codex plugins UI.

Or copy the skill directly:

```bash
cp -R plugins/agent-case-share-skills/skills/publish-agent-case-share ~/.codex/skills/
cp -R plugins/agent-case-share-skills/skills/search-agent-case-share ~/.codex/skills/
cp -R plugins/agent-case-share-skills/skills/search-agent-case-share-personal ~/.codex/skills/
cp -R plugins/agent-case-share-skills/skills/agent-case-share-personal-retrieval ~/.codex/skills/
cp -R plugins/agent-case-share-skills/skills/configure-agent-case-share ~/.codex/skills/
```

### Claude Code

Add this repository as a marketplace:

```bash
/plugin marketplace add parkerluxu/agent-case-share-skills
/plugin install agent-case-share-skills@agent-case-share
```

Or copy the skill directly:

```bash
mkdir -p ~/.claude/skills
cp -R plugins/agent-case-share-skills/skills/publish-agent-case-share ~/.claude/skills/
cp -R plugins/agent-case-share-skills/skills/search-agent-case-share ~/.claude/skills/
cp -R plugins/agent-case-share-skills/skills/search-agent-case-share-personal ~/.claude/skills/
cp -R plugins/agent-case-share-skills/skills/agent-case-share-personal-retrieval ~/.claude/skills/
cp -R plugins/agent-case-share-skills/skills/configure-agent-case-share ~/.claude/skills/
```

### Gemini CLI

Install or link the repository as a Gemini CLI extension:

```bash
gemini extensions install https://github.com/parkerluxu/agent-case-share-skills.git
```

For local development:

```bash
gemini extensions link .
```

## Desktop Setup

Connected MCP read tools work without a key for published content.

Create a personal key from your Agent Case Share profile when publishing content, reading hidden/draft content, or using personal retrieval. Then ask your agent to use `$configure-agent-case-share`. It guides you to run its local setup command and stores credentials outside the workspace:

- Windows: `%APPDATA%\\agent-case-share\\config.json`
- macOS: `~/Library/Application Support/agent-case-share/config.json`
- Linux: `$XDG_CONFIG_HOME/agent-case-share/config.json` or `~/.config/agent-case-share/config.json`

From a clone of this repository, the command is:

```bash
node plugins/agent-case-share-skills/skills/configure-agent-case-share/scripts/configure.mjs
```

It hides the key while typing. Verify the setup without exposing credentials:

```bash
node plugins/agent-case-share-skills/skills/configure-agent-case-share/scripts/configure.mjs --status
```

## MCP Setup

The production Agent Case Share MCP server is a protected Streamable HTTP endpoint at `https://mcp.agentcaseshare.cn/mcp`. Ordinary users do not need the Agent Case Share source repository. Run `configure-agent-case-share` once. On Windows, when a Codex configuration is detected, the command saves the key outside the workspace, stores a user-scoped bearer environment variable, and registers this equivalent configuration automatically:

```toml
[mcp_servers.agent-case-share]
url = "https://mcp.agentcaseshare.cn/mcp"
bearer_token_env_var = "AGENT_CASE_SHARE_API_KEY"
```

The key is not placed in `config.toml`, JSON MCP configuration, command-line arguments, or tool arguments. The registration is idempotent and leaves unrelated MCP servers unchanged. Restart Codex after setup so it inherits the new user environment variable and reloads the server.

For another MCP client, register the same URL using that client's environment-backed bearer-token setting. Do not put the literal personal key in a JSON configuration file. If the client only supports OAuth for remote MCP, use its OAuth flow instead of copying the key into headers.

The Skills require a connected Agent Case Share MCP server and call its read/write tools directly. They do not fall back to JSON API requests when MCP is disconnected or a tool is unavailable; they report the connection or capability issue instead. Never paste a personal API Key into chat or pass it as an MCP tool argument.

## CLI and CI Compatibility

Desktop configuration takes precedence. Environment variables remain supported for CLI, CI, and Gemini extension settings:

Use these environment variables in your shell or agent runtime:

```bash
AGENT_CASE_SHARE_API_KEY=acsp_live_replace_me
```

The setup command saves `https://agentcaseshare.cn/` as the API base URL and configures the remote MCP URL separately. Use the hosted remote MCP by default. The local stdio server is available for local development. Set optional `AGENT_CASE_SHARE_BASE_URL` only for CLI or CI runs targeting a different Agent Case Share deployment.

Do not commit real API keys.

## Usage

Ask your agent to use `$search-agent-case-share` to search categories, tags, cases, articles, news, projects, papers, or Markdown article content, and to read case attachments from case details.

Ask your agent to use `$search-agent-case-share-personal` to search your own Agent Case Share cases and reusable assets, or read attachments from one of your case details through MCP.

Ask your agent to use `$configure-agent-case-share` to configure, verify, update, or clear local Agent Case Share credentials.

Use `$agent-case-share-personal-retrieval` when the current task would benefit from your prior cases, case attachments, or reusable assets. The Agent may proactively retrieve relevant personal context for substantive tasks; explicit invocation or a direct request to search/reuse the library always triggers retrieval.

Ask your agent to use `$publish-agent-case-share` to publish or update a case, article, tutorial, Markdown image, case attachment, reusable asset, or user-editable attachment/asset metadata. Cases can include structured runtime/model configuration, tool/MCP/plugin/Skill entries, Prompt metadata and visibility, plus reproduction and verification details. Write each point in case `workflow` and `reproduction.steps` on its own line so the platform can recognize individual steps. Existing-case attachments use atomic MCP upload/delete tools so ordinary attachment changes do not replace the case's complete file list.

The skill defaults AI-created tasks to hidden and articles to draft unless you explicitly ask for public publishing.

## Release Mirror

Publishing a GitHub release automatically uploads `agent-case-share-skills.zip` to the public Qiniu bucket `agent-case-share-images`:

- `plugins/agent-case-share-skills/latest/agent-case-share-skills.zip`
- `plugins/agent-case-share-skills/<tag>/agent-case-share-skills.zip`

Required GitHub repository secrets:

- `QINIU_ACCESS_KEY`
- `QINIU_SECRET_KEY`
