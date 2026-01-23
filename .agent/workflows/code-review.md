---
description: Automated process for reviewing code changes to ensure adherence to Next.js 16/React 19 standards and project architecture.
---

# 🕵️ Automated Code Review Workflow

When asked to review code or a Pull Request, follow these steps:

## 1. Architectural Alignment
- Verify that features are correctly placed in `src/features/[feature_name]`.
- Ensure NO direct relative imports between features (must use `@/features/...`).
- check for "Barrel Exports" (index.ts) which are forbidden in this project.

## 2. React 19 & Next.js 16 Standards
- Check for proper use of Server vs Client components.
- Ensure `useActionState` is used for forms instead of older patterns.
- Verify Metadata is defined using the `Metadata` object in `layout.tsx` or `page.tsx`.

## 3. Security & Performance
- Confirm all API calls use the centralized `apiClient`.
- Check if Zod schemas are used for all input validation.
- Verify `next/image` usage with appropriate `priority` and `sizes`.

## 4. Output Format
Provide the review in three sections:
- ✅ **Strengths**: What was done correctly.
- ⚠️ **Required Changes**: Critical issues that MUST be fixed.
- 💡 **Suggestions**: Minor optimizations or best practices.
