# @movu/ui

Shared UI components for MovU frontend surfaces.

All app screens must import foundational UI from this package instead of recreating primitives locally. This keeps the admin dashboard and user PWA visually consistent while still allowing each app to compose domain-specific layouts.

## Import

```tsx
import { Alert, Badge, Button, Card, Input, Select, TabButton, Tabs } from "@movu/ui";
import "@movu/ui/styles.css";
```

Each app already aliases `@movu/ui` to `packages/ui/src/components` in its Vite and TypeScript config.

## Available Components

- `Button`: primary, secondary, ghost, danger, icon, wide
- `Card`: default, strong, dark, accent; supports `as` for semantic elements
- `Input`: text-like inputs
- `Select`: native select with MovU styling
- `Alert`: info, error, success, warning
- `Badge`: neutral, positive, negative, warning, info
- `Tabs` and `TabButton`: segmented controls

## Rules

- Do not define Button, Card, Input, Alert, Badge, Dialog, Tabs, Sheet, Switch, Select, or equivalent base components inside app folders.
- Do not use raw `<button>`, `<input>`, or `<select>` in `admin-dashboard/src` or `user-app/src`; use this package.
- App-level components may wrap shared primitives only for domain semantics, for example `StatusPill` wrapping `Badge` or `Field` wrapping `Input`.
- Page CSS may handle layout, spacing, and domain-specific composition, but not redefine base component visual systems.
- If a needed primitive is missing, add it here. If it is a standard shadcn component, install or port it into this package before using it in an app.

## Adding shadcn Components

This repo is currently Vite-based and not a preconfigured Tailwind/shadcn workspace. Use `components.json` at the repo root as the shadcn target contract, then install or adapt generated components into `packages/ui/src/components`.

Target paths:

- Components: `packages/ui/src/components`
- Shared styles: `packages/ui/src/styles.css`
- Utilities: `packages/ui/src/components/utils.ts`

After adding a component:

1. Export it from `packages/ui/src/components/index.ts`.
2. Add its styles or variants to `packages/ui/src/styles.css`.
3. Run both frontend builds.
4. Run the UI guard script from the root:

```bash
npm run ui:check
```
