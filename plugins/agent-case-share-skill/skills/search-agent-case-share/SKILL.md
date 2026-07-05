---
name: search-agent-case-share
description: Search, discover, and read public or authorized Agent Case Share knowledge-base content through JSON APIs. Use when the user asks an AI agent to find cases/tasks, articles/tutorials, AI news, open-source projects, papers, categories, tags, reusable assets, repositories, or Markdown content from an Agent Case Share site.
---

# Search Agent Case Share

Use this skill to treat Agent Case Share as a readable knowledge base.

## Safety

- Prefer public read APIs; no API key is needed for published content.
- Ask for the site base URL if it is missing.
- Ask for a personal API key only when the user needs hidden or draft content.
- Treat the API key as a secret. Do not print it, commit it, log it, or include it in generated files.
- Cite returned `url` values when summarizing or reusing content.

## Inputs

Confirm:

- Base URL, for example `https://your-domain.com`
- What to find or read: categories, tags, cases, articles, news, projects, papers, a specific slug, or a URL
- Optional personal API key for private content

Environment variables, when available:

- `AGENT_CASE_SHARE_BASE_URL`
- `AGENT_CASE_SHARE_API_KEY`

## Reference

For endpoint parameters, response shapes, and examples, read:

- `references/api.md`

## Workflow

1. Resolve the base URL from the user or `AGENT_CASE_SHARE_BASE_URL`.
2. Classify the request:
   - Category discovery -> `GET /api/categories`
   - Tag discovery -> `GET /api/tags`
   - General search -> `GET /api/search`
   - Case list/filtering -> `GET /api/tasks`
   - Case detail -> `GET /api/tasks/:slug`
   - Article Markdown -> `GET /api/articles/:slug`
3. If the user provides a site URL, infer the slug and endpoint:
   - `/tasks/:slug` -> `GET /api/tasks/:slug`
   - `/articles/:slug` -> `GET /api/articles/:slug`
4. Add `Authorization: Bearer <personal-api-key>` only for hidden or draft content.
5. Fetch JSON and inspect `items`, `task`, or `article`.
6. For summaries, preserve source links using each returned `url`.
7. If a query is broad, start with `limit=10`; broaden only when needed.
8. If the API returns `404`, report that the content was not found or not visible to the current credentials.

## Query Guidance

- Use `category` with category slugs from `/api/categories`.
- Use `tag` with tag names or slugs from `/api/tags`.
- Use `type` on `/api/search` only when the user asks for one content type.
- Use `/api/tasks/:slug` before `/api/articles/:slug` when the user wants the full case context.
- Use `/api/articles/:slug` when the user specifically needs Markdown content for rewriting, syncing, or summarizing.
