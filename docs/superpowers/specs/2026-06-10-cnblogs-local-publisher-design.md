# cnblogs Local Publisher — Design

Date: 2026-06-10

## Goal

Turn the existing `cnblogs/publish.py` into a **cnblogs-only, locally-run** publisher.
You choose which markdown file(s) to publish and run a command on your Mac. No GitHub
Actions, no push triggers, no Medium.

This is a minimal-change activation of the existing logic, not a rewrite.

## Usage

```
python cnblogs/publish.py path/to/article.md [more.md ...]
```

- Converts each markdown file to HTML and publishes to cnblogs via MetaWeblog (XML-RPC).
- Re-running the same file **updates** the existing post instead of creating a duplicate
  (idempotent via recorded post id).
- At least one file path is required. (The previous "no args = scan whole repo" behavior
  is removed — publishing is now an explicit per-file action.)

## Files

| File | Change |
|------|--------|
| `cnblogs/publish.py` | Strip all Medium code; add `.env` loading; drop `publish:` gating; require explicit file args; normalize state keys to repo-relative paths |
| `cnblogs/.env.example` | New. Template listing the 3 credential vars (committed) |
| `cnblogs/.env` | Real credentials. **Gitignored**, never committed |
| `cnblogs/requirements.txt` | New. `python-frontmatter`, `markdown`, `python-dotenv` |
| `cnblogs/.publish_state.json` | Idempotency state, committed so post ids survive across checkouts |
| `cnblogs/publish.yml` | **Deleted** (was the GitHub Actions workflow) |
| `cnblogs/README.md` | Rewritten: local-only usage; Medium and Actions sections removed |
| `.gitignore` | Add `cnblogs/.env` |

## Credentials

Loaded from `cnblogs/.env` via `python-dotenv`, falling back to existing environment
variables if already set. Three values:

- `CNBLOGS_BLOGNAME` — blog name from the URL (e.g. `geekchow`)
- `CNBLOGS_USERNAME` — login username
- `CNBLOGS_TOKEN` — MetaWeblog access token (cnblogs backend → 设置 → 其他设置)

If `CNBLOGS_TOKEN` is missing, the script exits with a clear error.

## Front matter

The `publish:` block is **dropped** — passing a file on the command line is the intent
to publish. Recognized front matter:

```yaml
---
title: "生产环境 RAG 的检索质量评估"      # required; file skipped if absent
date: 2026-06-10                          # optional
tags: [RAG, LLM, 评估]                    # optional → mt_keywords
cnblogs_categories: ["[随笔分类]AI"]       # optional → cnblogs categories
---
```

`canonical_url` (Medium-only) is no longer used.

## State & idempotency

- State file: `cnblogs/.publish_state.json`, anchored to the script's own directory so its
  location is independent of the current working directory.
- Keys: each file path normalized to a **repo-relative** path (repo root = parent of the
  script's directory), so re-running from any directory matches the same record.
- Value per file: `{ "cnblogs_id": "<postid>" }`. Presence of `cnblogs_id` → call
  `editPost` to update; absence → call `newPost` and store the returned id.

## Behavior flow

1. Load `cnblogs/.env`; build the `CnblogsClient` (error out if token missing).
2. For each file path argument that exists and ends in `.md`:
   - Load front matter; skip with a message if no `title`.
   - Convert `post.content` markdown → HTML5 (`fenced_code`, `tables`, `toc`,
     `codehilite`, `attr_list`).
   - Look up the repo-relative key in state.
   - `editPost` if a `cnblogs_id` exists, else `newPost` and record the id.
   - On error: print to stderr and continue to the next file.
3. Save state.

## Out of scope (per minimal-change goal)

- Mermaid pre-rendering — kept as a README caveat only.
- Image relative-path rewriting — kept as a README caveat only.
- Retries / advanced error handling — unchanged (print and continue).
- Jupyter `.ipynb` — convert to `.md` manually first, as noted in README.

## Verification

- Run against a throwaway/test markdown file → confirm a post appears on cnblogs and an id
  is recorded in `.publish_state.json`.
- Re-run the same file → confirm the existing post is updated (no duplicate created).
- Run with a file lacking `title` → confirm it is skipped with a message.
- Run with no `cnblogs/.env` and no env vars → confirm a clear "missing token" error.
