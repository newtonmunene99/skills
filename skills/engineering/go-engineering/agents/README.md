# Agent-specific config

This folder holds **product-specific** config files. They are read by the host (Codex, Cursor, etc.), not by the model. The core skill is defined in `SKILL.md` at the skill root.

## Current files

| File | Used by | Purpose |
|------|---------|---------|
| **openai.yaml** | Codex, GitHub Copilot (and any product that adopts this format) | UI display name, short description, default prompt. Optional: icons, brand color, policy, MCP/tool dependencies. |

## openai.yaml

- **interface.display_name** — Human-facing title in skill lists.
- **interface.short_description** — Short blurb (25–64 chars).
- **interface.default_prompt** — Example prompt when invoking the skill (should mention `$go-engineering`).

Optional fields you can add if needed:

- **interface.icon_small** / **interface.icon_large** — Paths to assets (e.g. `./assets/icon.svg`).
- **interface.brand_color** — Hex color for UI (e.g. `"#00ADD8"` for Go).
- **policy.allow_implicit_invocation** — Set to `false` to make the skill explicit-only (default `true`).
- **dependencies.tools** — List of MCP or other tools the skill can use.

## Other agents

**Cursor** and most other agents use only `SKILL.md` (and optional `scripts/`, `references/`, `assets/`). They do not define a separate manifest in `agents/`.

If a product documents its own manifest (e.g. `cursor.yaml`, `claude.yaml`), you can add it here. The [Agent Skills spec](https://agentskills.io/specification) does not require any file in `agents/`; this folder is for optional, product-specific metadata.
