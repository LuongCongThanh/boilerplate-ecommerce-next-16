# 📦 Import Alias Configuration & Best Practices

## ⚙️ TypeScript Configuration

Add these path aliases to your `tsconfig.json`:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/features/*": ["./src/features/*"],
      "@/shared/*": ["./src/shared/*"],
      "@/components/*": ["./src/shared/components/*"],
      "@/hooks/*": ["./src/shared/hooks/*"],
      "@/utils/*": ["./src/shared/lib/utils/*"],
      "@/types/*": ["./src/shared/types/*"],
      "@/config/*": ["./src/shared/config/*"]
    }
  }
}
```

## 📚 Import Best Practices

### ✅ RECOMMENDED

```typescript
// Use specific alias paths
import { Button } from '@/components/ui/button'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { authService } from '@/features/auth/services/authApi'
import { User, LoginInput } from '@/features/auth/types/auth.types'
import { cn } from '@/utils/cn'
import { API_ENDPOINTS } from '@/config/endpoints'

// Relative imports within same feature
// src/features/auth/components/LoginForm.tsx
import { useAuth } from '../hooks/useAuth'           // ✅ Same feature
import { authService } from '../services/authApi'    // ✅ Same feature
import { Button } from '@/components/ui/button'      // ✅ Shared resource
```

### ❌ AVOID

```typescript
// Deep relative paths
import { Button } from '../../../../shared/components/ui/button'
import { useAuth } from '../../../auth/hooks/useAuth'

// Barrel exports (index.ts)
import { User, LoginInput, authService } from '@/features/auth'

// Problems with barrel exports:
// ✗ Circular dependency issues
// ✗ Slower build times & HMR
// ✗ Poor tree-shaking
// ✗ Harder to track imports
// ✗ Extra maintenance overhead
```

## 🎯 Import Organization

Organize imports in this order:

```typescript
// 1. External libraries
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { z } from 'zod'

// 2. Internal alias imports (by layer)
import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/useToast'
import { cn } from '@/utils/cn'

// 3. Feature-specific imports
import { useAuth } from '@/features/auth/hooks/useAuth'
import { authService } from '@/features/auth/services/authApi'
import type { User } from '@/features/auth/types/auth.types'

// 4. Relative imports (same feature/folder)
import { LoginSchema } from './schemas'
import { validateInput } from './utils'

// 5. Styles (always last)
import './styles.css'
```

## 💡 Benefits: Direct Imports vs Barrel Exports

| Aspect | With index.ts | Without index.ts (Direct) |
|--------|--------------|---------------------------|
| **Build Speed** | Slower | ⚡ Faster |
| **HMR (Hot Reload)** | Slower | ⚡ Instant |
| **Circular Dependencies** | High risk | 🛡️ Minimal risk |
| **Tree Shaking** | Poor | 🌳 Excellent |
| **Bundle Size** | Larger | 📦 Smaller |
| **Maintenance** | Extra files | ✅ Less overhead |
| **Import Clarity** | Implicit paths | ✅ Explicit paths |
| **Debugging** | Harder to trace | ✅ Easy to trace |
| **IDE Auto-import** | Can break | ✅ Reliable |
| **Refactoring** | Risky | ✅ Safe |

## 📐 File Structure Without index.ts

```
src/
  features/
    auth/
      components/
        LoginForm.tsx              // Import: @/features/auth/components/LoginForm
        RegisterForm.tsx
      hooks/
        useAuth.ts                 // Import: @/features/auth/hooks/useAuth
        useLogin.ts
      services/
        authApi.ts                 // Import: @/features/auth/services/authApi
        authService.ts
      types/
        auth.types.ts              // Import: @/features/auth/types/auth.types
        session.types.ts
        
  shared/
    components/
      ui/
        button.tsx                 // Import: @/components/ui/button
        card.tsx
    hooks/
      useDebounce.ts               // Import: @/hooks/useDebounce
      useMediaQuery.ts
    lib/
      utils/
        cn.ts                      // Import: @/utils/cn
        formatters.ts
```

## 🚫 When to Use Relative Imports

Use relative imports **only** when importing within the same feature:

```typescript
// ✅ Good - Within same feature
src/features/auth/components/LoginForm.tsx
  ↓
import { useAuth } from '../hooks/useAuth'
import { authService } from '../services/authApi'
import type { LoginInput } from '../types/auth.types'

// ❌ Bad - Cross-feature relative imports
import { useCart } from '../../cart/hooks/useCart'  // Use alias instead

// ✅ Good - Use alias for cross-feature
import { useCart } from '@/features/cart/hooks/useCart'
```

## 📝 ESLint Configuration (Optional)

Enforce import order with `eslint-plugin-import`:

```json
{
  "plugins": ["import"],
  "rules": {
    "import/order": ["error", {
      "groups": [
        "builtin",
        "external",
        "internal",
        ["parent", "sibling"],
        "index",
        "object",
        "type"
      ],
      "pathGroups": [
        {
          "pattern": "@/**",
          "group": "internal",
          "position": "after"
        }
      ],
      "newlines-between": "always",
      "alphabetize": {
        "order": "asc",
        "caseInsensitive": true
      }
    }]
  }
}
```

## 🔧 Next.js Configuration

Ensure your `next.config.ts` doesn't override paths:

```typescript
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // No need to configure paths here - tsconfig.json handles it
  experimental: {
    optimizePackageImports: ['@/components', '@/features']  // Optional: optimize imports
  }
}

export default nextConfig
```

## ✨ VS Code Settings (Optional)

Add to `.vscode/settings.json` for better auto-imports:

```json
{
  "typescript.preferences.importModuleSpecifier": "non-relative",
  "javascript.preferences.importModuleSpecifier": "non-relative",
  "typescript.updateImportsOnFileMove.enabled": "always",
  "javascript.updateImportsOnFileMove.enabled": "always"
}
```

---

**Summary:** Use import alias `@/` for explicit, fast, and maintainable imports. Avoid `index.ts` barrel exports.
