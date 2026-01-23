---
description: Structured workflow for identifying, reproducing, and fixing bugs.
---

# 🐛 Bug Fixing Workflow

Follow these steps when tasked with fixing a bug or resolving an issue:

## 1. Investigation & Reproduction
- **Analyze Logs**: Check console logs and error messages.
- **Reproduction Case**: Create a minimal reproduction step or a failing test case (Playwright/Vitest).
- **Find Root Cause**: Trace the issue back to the specific feature logic in `src/features/`.

## 2. Planning the Fix
- Verify if the fix violates any architectural rules (Barrel exports, shared logic).
- Check `docs/README.md` for proper error handling patterns.

## 3. Implementation
- Apply the fix using React 19 standards (`useActionState` for form errors, etc.).
- Ensure Zod validation is updated if the issue was related to data types.

## 4. Verification
- Run the reproduction test to ensure it now passes.
- Run `npm run lint` and `npm run type-check` to prevent regressions.
- Perform a manual check of related features.

## 5. Documentation
- If the bug was a critical architectural flaw, update `docs/MIGRATION.md` or `ARCHITECTURE.md`.
