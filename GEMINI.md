# Agent Case Share

Use `plugins/agent-case-share-skills/skills/configure-agent-case-share` when the user asks to configure, connect, update, verify, or clear Agent Case Share MCP credentials. Do not ask users to paste keys into chat.

Use `plugins/agent-case-share-skills/skills/capture-agent-case-share` when the user asks to capture, convert, locally export, or upload their Agent environment, current or selected historical Session, or both to a case. Honor environment-only, Session-only, custom scope, and export-only requests. Use generic exports for host formats without a native adapter.

Use `plugins/agent-case-share-skills/skills/publish-agent-case-share` when the user asks to publish or edit Agent Case Share tasks, cases, immutable Agent environment snapshots, explicit Session transcripts, case videos, articles, tutorials, Markdown images, case attachments, reusable assets, public community discussions, or public discussion replies.

Use `plugins/agent-case-share-skills/skills/search-agent-case-share` when the user asks to search, discover, or read Agent Case Share categories, tags, cases, Agent environments, Session transcripts, case videos, case attachments, articles, AI news, public projects, papers, repositories, reusable assets, Markdown article content, public community discussions, approved verifications, community topics, or content-linked community context.

Use `plugins/agent-case-share-skills/skills/search-agent-case-share-personal` when the user asks to list or read saved content, or to search their own cases, Agent environments, Sessions, videos, attachments, or reusable assets.

Use `plugins/agent-case-share-skills/skills/agent-case-share-personal-retrieval` when the current task would benefit from the user's relevant saved items or prior cases, Agent environments, Sessions, videos, attachments, or reusable assets.
