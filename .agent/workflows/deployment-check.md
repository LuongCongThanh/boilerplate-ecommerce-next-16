---
description: Checklist for pre-deployment verification to ensure production stability.
---

# 🚀 Deployment Check Workflow

Execute these checks before any major deployment or PR merge to production:

## 1. Environment & Build
- [ ] **Env Check**: Verify all new environment variables are in `.env.example`.
- [ ] **Build Check**: Run `npm run build` locally to ensure no compilation errors.
- [ ] **Type Check**: Run `npm run type-check`.

## 2. Quality & Performance
- [ ] **Lint Check**: Run `npm run lint`.
- [ ] **Test Coverage**: Ensure `npm test` passes and coverage is maintained.
- [ ] **E2E Tests**: Run `npm run test:e2e` for critical flows (Checkout, Auth).
- [ ] **Performance Audit**: Check `docs/PERFORMANCE.md` targets.

## 3. Security
- [ ] **Validator Check**: Ensure all API inputs use Zod.
- [ ] **Auth Check**: Verify middleware protection for sensitive routes.

## 4. Documentation
- [ ] **Changelog**: Update `docs/README.md` if new features were added.
- [ ] **Index**: Sync `docs/DOCS_INDEX.md` if new files were created.
