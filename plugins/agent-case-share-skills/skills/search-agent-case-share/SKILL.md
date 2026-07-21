---
name: search-agent-case-share
description: Search, discover, and read public or authorized Agent Case Share knowledge-base content through JSON APIs. Use when the user asks an AI agent to find cases/tasks, articles/tutorials, AI news, public projects, papers, categories, tags, reusable assets, repositories, or Markdown content from an Agent Case Share site.
---

# Search Agent Case Share

Use this skill to treat Agent Case Share as a readable knowledge base.

## Safety

- Prefer public read APIs; no API key is needed for published content.
- Use `https://agentcaseshare.cn/` as the default base URL; ask only for a different site if the user mentions one.
- For hidden or draft content, resolve a personal API key from the Agent Case Share user configuration file before environment variables. If it is missing, invoke `$configure-agent-case-share`; do not ask the user to paste a key into chat.
- Treat the API key as a secret. Do not print it, commit it, log it, or include it in generated files.
- Set `User-Agent: AgentCaseShare-AIClient/1.0` and `Accept: application/json` explicitly on every Agent Case Share HTTP request. Do not rely on the default User-Agent of Python `urllib`, curl, Node `fetch`, or any other client, and do not impersonate a browser User-Agent.
- For JSON requests, also set `Content-Type: application/json`; retain `Authorization: Bearer <personal-api-key>` whenever the existing endpoint rules require it. For downloads, send the fixed User-Agent and Accept headers even though the response is binary.
- If a response body contains `cloudflare_error: true`, `error_code: 1010`, or `browser_signature_banned`, do not retry automatically. Report that Cloudflare blocked the request before it reached the API, and ask the site administrator to review the Browser Integrity Check rule for `/api/*` and allow `AgentCaseShare-AIClient/1.0`.
- Cite returned `url` values when summarizing or reusing content.

## Inputs

Confirm:

- Base URL, default `https://agentcaseshare.cn/`
- What to find or read: categories, tags, cases, articles, news, projects, papers, assets, a specific slug/id, or a URL
- Optional personal API key for private content

User configuration takes precedence and is created by `$configure-agent-case-share`:

- Windows: `%APPDATA%\\agent-case-share\\config.json`
- macOS: `~/Library/Application Support/agent-case-share/config.json`
- Linux: `$XDG_CONFIG_HOME/agent-case-share/config.json` or `~/.config/agent-case-share/config.json`

Compatible environment variables, when available:

- `AGENT_CASE_SHARE_BASE_URL`
- `AGENT_CASE_SHARE_API_KEY`

## Reference

For endpoint parameters, response shapes, and examples, read:

- `references/api.md`

## Slug Handling

- Treat every API-returned slug as an opaque identifier. Newly generated slugs use `case-xxxxxxxx`, `article-xxxxxxxx`, `project-xxxxxxxx`, or `paper-xxxxxxxx` according to content type.
- Use returned `url` and `taskUrl` values directly; they are already percent-encoded. Do not encode them again.
- When constructing an API path from a raw `slug` field, encode that path segment exactly once with `encodeURIComponent`.
- When extracting a slug from an already encoded site URL before rebuilding a different path, decode the path segment once, then encode it once for the new path.
- Do not derive a slug from a title or name and do not assume that a case slug starts with `task-`; cases use the `case-` prefix.

## Workflow

1. Resolve settings from the Agent Case Share user configuration file, then `AGENT_CASE_SHARE_BASE_URL`, then the default base URL `https://agentcaseshare.cn/`. For private requests, also resolve `AGENT_CASE_SHARE_API_KEY`; if no key is available, invoke `$configure-agent-case-share`.
2. Classify the request:
   - Category discovery -> `GET /api/categories`
   - Tag discovery -> `GET /api/tags`
   - General search -> `GET /api/search`
   - Case list/filtering -> `GET /api/tasks`
   - Case detail -> `GET /api/tasks/:slug`
   - Article Markdown -> `GET /api/articles/:slug`
   - Project detail -> `GET /api/projects/:slug`
   - Paper detail -> `GET /api/papers/:slug`
   - Public asset list/filtering -> `GET /api/assets`
3. If the user provides a site URL, infer the slug and endpoint, preserving the path segment's single percent-encoding:
   - `/tasks/:slug` -> `GET /api/tasks/:slug`
   - `/articles/:slug` -> `GET /api/articles/:slug`
   - `/projects/:slug` -> `GET /api/projects/:slug`
   - `/papers/:slug` -> `GET /api/papers/:slug`
   - `/assets/:id` -> use `GET /api/assets` with `q`/filters when no public detail endpoint is available
4. Set the required explicit `User-Agent` and `Accept` headers; add `Content-Type: application/json` for JSON requests. Add `Authorization: Bearer <personal-api-key>` only for hidden or draft content.
5. Fetch JSON and inspect `items`, `task`, `article`, `project`, or `paper`.
6. For summaries, preserve source links using each returned `url`.
7. If a query is broad, start with `limit=10`; broaden only when needed.
8. If the API returns `404`, report that the content was not found or not visible to the current credentials.
9. On a Cloudflare 1010 signature block, do not retry; report that the request was intercepted before the API and direct the site administrator to allow the fixed AI client User-Agent for `/api/*`.

## Query Guidance

- Use `category` with category slugs from `/api/categories`.
- Use `tag` with tag names or slugs from `/api/tags`.
- Use `type` on `/api/search` only when the user asks for one content type: `task`, `article`, `news`, `project`, or `paper`.
- Use `/api/tasks/:slug` before `/api/articles/:slug` when the user wants the full case context.
- Use `/api/articles/:slug` when the user specifically needs Markdown content for rewriting, syncing, or summarizing.
- Use `/api/projects/:slug` when the user needs the full public project description, repo/site/tutorial URLs, license, or tags.
- Use `/api/papers/:slug` when the user needs full paper metadata, links, DOI, keywords, notes, or tags.
- Use `/api/assets` for public asset discovery across the site; use `category` when the user asks for category-specific assets.

## Download Public Asset

To download a public asset file (skill package, prompt template, workflow definition, etc.):

1. Obtain the `downloadUrl` from search results (`/api/search`), asset list (`/api/assets`), or asset detail (`/api/assets/:id`). Format: `/api/assets/:id/download`.
2. Make a `GET` request to that URL with `User-Agent: AgentCaseShare-AIClient/1.0` and `Accept: application/json`. No authentication is required for public assets.
3. The response streams the file binary with appropriate `Content-Type` and `Content-Disposition` headers.
4. Save the file using the `fileName` from the asset metadata (or derive from `downloadUrl`).

**Note**: The same `/api/assets/:id/download` endpoint serves both public and authorized private downloads. For personal/hidden assets, include `Authorization: Bearer <personal-api-key>` header.
