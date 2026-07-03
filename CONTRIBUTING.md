# Contributing

## UI Component Rules

MovU uses a shared UI package at `packages/ui/src/components`.

Required:

- Always import foundational UI from `@movu/ui`.
- Use `Button`, `Card`, `Input`, `Select`, `Alert`, `Badge`, `Tabs`, and related primitives from `packages/ui`.
- Keep page and feature components focused on composition and domain behavior.
- Keep styling consistent with the MovU tokens already defined in app CSS and `packages/ui/src/styles.css`.

Not allowed:

- Recreating Button, Card, Input, Alert, Badge, Dialog, Tabs, Sheet, Switch, Select, or equivalent base primitives inside `admin-dashboard/src` or `user-app/src`.
- Raw `<button>`, `<input>`, or `<select>` inside app source.
- Introducing a second visual system or mixing unrelated component libraries.

If a primitive is missing:

1. Add it under `packages/ui/src/components`.
2. Prefer a shadcn component when the repo is configured for it, or port the generated component into the shared UI package.
3. Export it from `packages/ui/src/components/index.ts`.
4. Use it from app code via `@movu/ui`.

Run before handoff:

```bash
npm run ui:check
cd user-app && npm run build
cd ../admin-dashboard && npm run build
PYTHONPATH=backend .venv/bin/pytest backend/tests -q
```
