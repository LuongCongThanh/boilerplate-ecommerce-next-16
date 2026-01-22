# 🔄 Migration Guide (v2 to v3)

## Overview of Major Changes

| Category | v2.0 | v3.0 | Impact |
|----------|------|------|--------|
| **Next.js** | 14.x | 16.x | Breaking |
| **React** | 18.x | 19.x | Breaking |
| **Auth** | NextAuth v5 (beta) | NextAuth v4 (stable) | Breaking |
| **State** | Context API | React Query + Zustand | Major |
| **Routing** | Pages Router | App Router | Breaking |
| **Testing** | Jest | Vitest | Minor |
| **Styling** | CSS Modules | Tailwind CSS | Major |

## Breaking Changes

### 1. App Router Migration

**v2.0 (Pages Router):**
```typescript
// pages/products/[id].tsx
import { GetServerSideProps } from 'next'

export const getServerSideProps: GetServerSideProps = async ({ params }) => {
  const product = await fetchProduct(params.id)
  return { props: { product } }
}

export default function ProductPage({ product }) {
  return <div>{product.name}</div>
}
```

**v3.0 (App Router):**
```typescript
// app/products/[id]/page.tsx
import { notFound } from 'next/navigation'

interface Props {
  params: { id: string }
}

export default async function ProductPage({ params }: Props) {
  const product = await fetchProduct(params.id)
  
  if (!product) {
    notFound()
  }
  
  return <div>{product.name}</div>
}

// Generate static params
export async function generateStaticParams() {
  const products = await fetchAllProducts()
  return products.map((product) => ({ id: product.id }))
}
```

### 2. Authentication Migration

**v2.0 (NextAuth v5 beta):**
```typescript
// auth.ts
import NextAuth from 'next-auth'

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [/* ... */]
})
```

**v3.0 (NextAuth v4 stable):**
```typescript
// app/api/auth/[...nextauth]/route.ts
import NextAuth, { NextAuthOptions } from 'next-auth'

export const authOptions: NextAuthOptions = {
  providers: [/* ... */],
  callbacks: {
    async jwt({ token, user }) { /* ... */ },
    async session({ session, token }) { /* ... */ }
  }
}

const handler = NextAuth(authOptions)
export { handler as GET, handler as POST }
```

### 3. Client Components Migration

**v2.0:**
```typescript
// All components were client by default
import { useState } from 'react'

export default function Counter() {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount(count + 1)}>{count}</button>
}
```

**v3.0:**
```typescript
// Must explicitly mark as client component
'use client'

import { useState } from 'react'

export default function Counter() {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount(count + 1)}>{count}</button>
}
```

### 4. API Routes Migration

**v2.0:**
```typescript
// pages/api/products.ts
import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === 'GET') {
    const products = await fetchProducts()
    res.status(200).json(products)
  }
}
```

**v3.0:**
```typescript
// app/api/products/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const products = await fetchProducts()
  return NextResponse.json(products)
}

export async function POST(request: NextRequest) {
  const body = await request.json()
  const product = await createProduct(body)
  return NextResponse.json(product, { status: 201 })
}
```

### 5. Metadata Migration

**v2.0:**
```typescript
// pages/products/[id].tsx
import Head from 'next/head'

export default function ProductPage({ product }) {
  return (
    <>
      <Head>
        <title>{product.name}</title>
        <meta name="description" content={product.description} />
      </Head>
      <div>{product.name}</div>
    </>
  )
}
```

**v3.0:**
```typescript
// app/products/[id]/page.tsx
import { Metadata } from 'next'

interface Props {
  params: { id: string }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const product = await fetchProduct(params.id)
  
  return {
    title: product.name,
    description: product.description,
    openGraph: {
      title: product.name,
      description: product.description,
      images: [product.image]
    }
  }
}

export default async function ProductPage({ params }: Props) {
  const product = await fetchProduct(params.id)
  return <div>{product.name}</div>
}
```

## Step-by-Step Migration Process

### Phase 1: Preparation (Week 1)

```bash
# 1. Create a new branch
git checkout -b migration/v3

# 2. Backup current codebase
git tag v2-backup

# 3. Update dependencies
npm install next@latest react@latest react-dom@latest
npm install next-auth@4 --save-exact

# 4. Install new dependencies
npm install @tanstack/react-query zustand
npm install -D vitest @vitejs/plugin-react
```

### Phase 2: Structure Changes (Week 2)

1. **Create new app directory:**
   ```bash
   mkdir -p src/app
   mkdir -p src/features
   mkdir -p src/shared
   ```

2. **Move pages to app router:**
   - Convert `pages/index.tsx` → `app/page.tsx`
   - Convert `pages/_app.tsx` → `app/layout.tsx`
   - Convert `pages/products/[id].tsx` → `app/products/[id]/page.tsx`

3. **Update imports:**
   ```bash
   # Find and replace imports
   find src -type f -name "*.tsx" -exec sed -i '' 's|from "pages/|from "@/app/|g' {} +
   ```

### Phase 3: Feature Migration (Week 3-4)

1. **Migrate authentication:**
   - Update NextAuth configuration
   - Convert auth pages to app router
   - Update session hooks

2. **Migrate state management:**
   ```typescript
   // Old: Context API
   const { cart } = useContext(CartContext)
   
   // New: Zustand + React Query
   const cart = useCartStore((state) => state.cart)
   const { data: products } = useQuery({ queryKey: ['products'], queryFn: fetchProducts })
   ```

3. **Update API calls:**
   - Replace `fetch` with new API client
   - Add error handling
   - Implement retry logic

### Phase 4: Testing & Validation (Week 5)

```bash
# Run all tests
npm run test
npm run test:e2e

# Check for TypeScript errors
npm run type-check

# Build for production
npm run build

# Test production build locally
npm run start
```

### Phase 5: Deployment (Week 6)

1. **Deploy to staging:**
   ```bash
   vercel --env-file .env.staging
   ```

2. **Run smoke tests on staging**

3. **Deploy to production:**
   ```bash
   vercel --prod
   ```

## Migration Checklist

- [ ] Dependencies updated to latest versions
- [ ] App Router structure created
- [ ] All pages migrated to app directory
- [ ] API routes converted to route handlers
- [ ] Client components marked with 'use client'
- [ ] Server components optimized (no useState, useEffect)
- [ ] Metadata generated with generateMetadata
- [ ] Authentication migrated to NextAuth v4
- [ ] State management updated (React Query + Zustand)
- [ ] All imports updated to use @ alias
- [ ] Environment variables validated with Zod
- [ ] Tests updated and passing
- [ ] Build succeeds without errors
- [ ] Performance benchmarks meet targets
- [ ] Staging deployment successful
- [ ] Production deployment successful

## Common Migration Issues

### Issue 1: Hydration Mismatches

**Problem:**
```
Error: Hydration failed because the initial UI does not match what was rendered on the server.
```

**Solution:**
```typescript
// Use dynamic imports for client-only components
import dynamic from 'next/dynamic'

const ClientComponent = dynamic(
  () => import('@/components/ClientComponent'),
  { ssr: false }
)
```

### Issue 2: useSearchParams in Server Component

**Problem:**
```typescript
// This won't work in server components
import { useSearchParams } from 'next/navigation'

export default function Page() {
  const searchParams = useSearchParams() // Error!
}
```

**Solution:**
```typescript
// Use searchParams prop in server components
export default function Page({ searchParams }: { searchParams: { query: string } }) {
  const query = searchParams.query
}
```

### Issue 3: Session Not Available

**Problem:**
```typescript
// useSession() returns null after migration
const { data: session } = useSession()
```

**Solution:**
```typescript
// Ensure SessionProvider wraps your app
// app/layout.tsx
import { SessionProvider } from 'next-auth/react'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <SessionProvider>
          {children}
        </SessionProvider>
      </body>
    </html>
  )
}
```

## Rollback Plan

If critical issues arise:

```bash
# 1. Rollback deployment
vercel rollback

# 2. Revert to v2 codebase
git checkout v2-backup

# 3. Reinstall v2 dependencies
npm ci

# 4. Redeploy v2
npm run build && vercel --prod
```

## Post-Migration Tasks

### 1. Update Documentation
- [ ] Update README with new structure
- [ ] Update onboarding docs for new developers
- [ ] Create migration notes for team

### 2. Performance Monitoring
- [ ] Set up Lighthouse CI
- [ ] Monitor Core Web Vitals
- [ ] Track error rates in Sentry

### 3. Team Training
- [ ] Conduct App Router workshop
- [ ] Share best practices document
- [ ] Create coding guidelines

### 4. Cleanup
- [ ] Remove old pages directory
- [ ] Delete unused dependencies
- [ ] Archive v2 documentation

## Getting Help

If you encounter issues during migration:
- Check [Next.js Migration Guide](https://nextjs.org/docs/app/building-your-application/upgrading)
- Join [Next.js Discord](https://nextjs.org/discord)
- Review [GitHub Discussions](https://github.com/vercel/next.js/discussions)
- Contact team lead for support
