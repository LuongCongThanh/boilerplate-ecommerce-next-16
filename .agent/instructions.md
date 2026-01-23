# 🌐 Universal AI Agent Instructions

This project follows a strict "Production-Grade" architecture for Next.js 16 and React 19. All AI agents (Antigravity, Claude Code, Cursor, etc.) MUST adhere to these rules.

## 1. Project Identity
- **Name**: Enterprise Next.js 16 E-commerce Boilerplate
- **Year**: 2026 (Future-forward tech stack)
- **Framework**: Next.js 16 (App Router), React 19

## 2. Directory Hierarchy (Strict)
- `src/app`: Routes, Layouts, Metadata.
- `src/features/[feature_name]`: Business logic (components, hooks, services, store, types, utils).
- `src/shared`: Generic components (UI), hooks, and global utilities.
- `docs/`: Source of truth for architecture, performance, and migration.

## 3. Technology Guardrails
- **Components**: Server Components by default. Use React 19 `use` hook and action patterns.
- **Styling**: Tailwind CSS + shadcn/ui.
- **State**: React Query (Server), Zustand (Client).
- **Imports**: Always use absolute paths with `@/` alias. **NO RELATIVE IMPORTS**.
- **No Barrel Exports**: Avoid `index.ts` in subdirectories to prevent circular dependencies.

## 4. Agent Checklist
Before providing any response or code change:
1. Scan `docs/ARCHITECTURE.md` to ensure architectural alignment.
2. If modifying routes, check `docs/MIGRATION.md` for proper App Router patterns.
3. If adding a new feature, ensure it is encapsulated in `src/features/`.
4. Check `.cursorrules` or `.clauderules` for tool-specific formatting if applicable.

## 5. Security Mantra
- Middleware handles security headers and role-based access.
- Always validate input with Zod schemas.
- Use the custom `apiClient` in `src/shared/services/apiClient.ts` for all external requests.
