---
description: Structured workflow for implementing new features from design to production-ready code.
---

# 🚀 Feature Implementation Workflow

Use this workflow when the user asks to "implement", "create", or "build" a new feature.

## Phase 1: Research
- Scan `docs/ARCHITECTURE.md` to understand where this feature fits.
- Check existing `src/shared` components to avoid rebuilding UI elements.

## Phase 2: Design-to-Code (If Figma is available)
- Request the specific Figma frame name if not provided.
- Map Figma styles to Tailwind CSS tokens in the project.

## Phase 3: Scaffolding
- Create the feature structure in `src/features/[name]`:
  - `components/`
  - `hooks/`
  - `services/`
  - `types/`
- Add necessary environment variables to `.env.example`.

## Phase 4: Implementation
- Implement logic using Server Actions and React 19 hooks.
- Apply strict Zod validation for all data structures.

## Phase 5: Verification
- Create a basic Playwright test for the main success path.
- Run `npm run type-check` and `npm run lint` (implicitly suggest these).
