# Agent Case Share Skill

Reusable AI-agent skills for searching, reading, publishing, and editing Agent Case Share content.

## Install

### Codex

Add this repository as a marketplace:

```bash
codex plugin marketplace add parkerluxu/agent-case-share-skill
```

Then install `agent-case-share-skill` from the Codex plugins UI.

Or copy the skill directly:

```bash
cp -R plugins/agent-case-share-skill/skills/publish-agent-case-share ~/.codex/skills/
cp -R plugins/agent-case-share-skill/skills/search-agent-case-share ~/.codex/skills/
cp -R plugins/agent-case-share-skill/skills/search-agent-case-share-personal ~/.codex/skills/
cp -R plugins/agent-case-share-skill/skills/agent-case-share-auto-retrieval ~/.codex/skills/
cp -R plugins/agent-case-share-skill/skills/configure-agent-case-share ~/.codex/skills/
```

### Claude Code

Add this repository as a marketplace:

```bash
/plugin marketplace add parkerluxu/agent-case-share-skill
/plugin install agent-case-share-skill@agent-case-share
```

Or copy the skill directly:

```bash
mkdir -p ~/.claude/skills
cp -R plugins/agent-case-share-skill/skills/publish-agent-case-share ~/.claude/skills/
cp -R plugins/agent-case-share-skill/skills/search-agent-case-share ~/.claude/skills/
cp -R plugins/agent-case-share-skill/skills/search-agent-case-share-personal ~/.claude/skills/
cp -R plugins/agent-case-share-skill/skills/agent-case-share-auto-retrieval ~/.claude/skills/
cp -R plugins/agent-case-share-skill/skills/configure-agent-case-share ~/.claude/skills/
```

### Gemini CLI

Install or link the repository as a Gemini CLI extension:

```bash
gemini extensions install https://github.com/parkerluxu/agent-case-share-skill.git
```

For local development:

```bash
gemini extensions link .
```

## Desktop Setup

Search and read APIs work without a key for published content.

Create a personal API key from your Agent Case Share `/profile` page when publishing content, reading hidden/draft content, or using personal retrieval. Then ask your agent to use `$configure-agent-case-share`. It guides you to run its local setup command and stores credentials outside the workspace:

- Windows: `%APPDATA%\\agent-case-share\\config.json`
- macOS: `~/Library/Application Support/agent-case-share/config.json`
- Linux: `$XDG_CONFIG_HOME/agent-case-share/config.json` or `~/.config/agent-case-share/config.json`

From a clone of this repository, the command is:

```bash
node plugins/agent-case-share-skill/skills/configure-agent-case-share/scripts/configure.mjs
```

It hides the key while typing. Verify the setup without exposing credentials:

```bash
node plugins/agent-case-share-skill/skills/configure-agent-case-share/scripts/configure.mjs --status
```

## CLI and CI Compatibility

Desktop configuration takes precedence. Environment variables remain supported for CLI, CI, and Gemini extension settings:

Use these environment variables in your shell or agent runtime:

```bash
AGENT_CASE_SHARE_API_KEY=acsp_live_replace_me
```

The base URL defaults to `https://agentcaseshare.cn/`. Set `AGENT_CASE_SHARE_BASE_URL` only when targeting a different Agent Case Share deployment.

Do not commit real API keys.

## Usage

Ask your agent to use `$search-agent-case-share` to search categories, tags, cases, articles, news, projects, papers, or Markdown article content, and to read case, project, paper, or article details by URL or slug.

Ask your agent to use `$search-agent-case-share-personal` to search your own Agent Case Share cases and reusable assets with a personal API key.

Ask your agent to use `$configure-agent-case-share` to configure, verify, update, or clear local Agent Case Share credentials.

Ask your agent to use `$agent-case-share-auto-retrieval` to retrieve relevant cases and reusable assets from your personal library during a conversation.

Ask your agent to use `$publish-agent-case-share` to publish or update a case, article, tutorial, Markdown image, reusable asset, or asset metadata.

The skill defaults AI-created tasks to hidden and articles to draft unless you explicitly ask for public publishing.

## Release Mirror

Publishing a GitHub release automatically uploads `agent-case-share-skill.zip` to the public Qiniu bucket `agent-case-share-images`:

- `plugins/agent-case-share-skill/latest/agent-case-share-skill.zip`
- `plugins/agent-case-share-skill/<tag>/agent-case-share-skill.zip`

Required GitHub repository secrets:

- `QINIU_ACCESS_KEY`
- `QINIU_SECRET_KEY`
