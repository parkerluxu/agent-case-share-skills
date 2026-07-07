---
name: search-agent-case-share-personal
description: Search and read the authenticated user's personal Agent Case Share library through `/api/me/*` JSON APIs. Use when the user asks an AI agent to find, list, retrieve, inspect, or summarize "my" Agent Case Share cases, personal cases, personal reusable assets, uploaded assets, hidden/draft user-owned content, or previous user-owned library items.
---

# Search Personal Agent Case Share

Use this skill to query the current user's private Agent Case Share library.

## Safety

- Require a signed-in browser session or `Authorization: Bearer <personal-api-key>` for every `/api/me/*` request.
- Ask for the personal API key if it is missing and no browser session is available.
- Treat the API key as a secret. Do not print it, commit it, log it, or include it in generated files.
- Use `https://agentcaseshare.cn/` as the default base URL; ask only for a different site if the user mentions one.
- Do not use public endpoints when the user specifically asks for "my" content, because public endpoints may omit hidden, draft, or user-owned context.

## Inputs

Confirm:

- Base URL, default `https://agentcaseshare.cn/`
- Personal API key generated from `/profile`, unless a signed-in browser session is available
- Whether the user wants personal cases, personal assets, one case/asset detail, or mixed personal search

Environment variables, when available:

- `AGENT_CASE_SHARE_BASE_URL`
- `AGENT_CASE_SHARE_API_KEY`

## Reference

For endpoint parameters, response shapes, and examples, read:

- `references/api.md`

## Workflow

1. Resolve the base URL from `AGENT_CASE_SHARE_BASE_URL`, the user, or default to `https://agentcaseshare.cn/`.
2. Use `Authorization: Bearer <personal-api-key>` for external scripts and agents.
3. Classify the request:
   - Search personal cases and assets together -> `GET /api/me/search`
   - List/filter personal cases -> `GET /api/me/cases`
   - Read one personal case -> `GET /api/me/cases/:slug`
   - List/filter personal assets -> `GET /api/me/assets`
   - Read one personal asset -> `GET /api/me/assets/:id`
4. If the user provides a URL, infer:
   - `/tasks/:slug` -> `GET /api/me/cases/:slug`
   - `/assets/:id` -> `GET /api/me/assets/:id`
5. Fetch JSON and inspect `items`, `case`, or `asset`.
6. Preserve returned `url` and `downloadUrl` values when reporting results.
7. If the user wants to edit the asset after finding it, hand off the returned asset `id` to `$publish-agent-case-share`, which owns `PATCH /api/assets/:id`.
8. If a query is broad, start with `limit=10`; use pagination only when needed.
9. On `401`, ask for a valid personal API key or signed-in session.
10. On `404`, report that the item was not found in the authenticated user's library.

## Query Guidance

- Use `/api/me/search` for fast recall across the user's cases and assets.
- Use `/api/me/cases` when the user needs status/category/tag filters or pagination for personal cases.
- Use `/api/me/assets` when the user needs asset `type`, `source`, `status`, or pagination filters.
- Omit `status` on `/api/me/cases` and `/api/me/assets` when the user wants all personal statuses; send `status=PUBLISHED`, `HIDDEN`, or `DRAFT` only when requested.
- Use `/api/me/cases/:slug` before article endpoints when the user wants case context, repositories, reusable assets, or review notes for their own case.
