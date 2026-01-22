# 🏛️ Architecture Overview

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Browser/User]
        PWA[PWA/Mobile]
    end
    
    subgraph "Next.js Application"
        subgraph "Edge Layer"
            Middleware[Middleware<br/>Auth, Security, i18n]
        end
        
        subgraph "App Router"
            Pages[Pages/Routes<br/>SSR/SSG/ISR]
            API[API Routes<br/>Backend Proxy]
        end
        
        subgraph "Feature Modules"
            Auth[Auth Module]
            Product[Product Module]
            Cart[Cart Module]
            Checkout[Checkout Module]
            Order[Order Module]
        end
        
        subgraph "Shared Layer"
            Components[Shared Components]
            Hooks[Custom Hooks]
            Utils[Utilities]
            Store[State Management<br/>Zustand + React Query]
        end
    end
    
    subgraph "External Services"
        BackendAPI[Backend REST API]
        OAuth[OAuth Providers<br/>Google, GitHub]
        Payment[Payment Gateway<br/>Stripe]
        CDN[CDN/Storage]
        Monitoring[Monitoring<br/>Sentry]
    end
    
    Browser --> Middleware
    PWA --> Middleware
    Middleware --> Pages
    Middleware --> API
    
    Pages --> Auth
    Pages --> Product
    Pages --> Cart
    Pages --> Checkout
    Pages --> Order
    
    Auth --> Components
    Product --> Components
    Cart --> Components
    Checkout --> Components
    Order --> Components
    
    Components --> Hooks
    Components --> Store
    Hooks --> Utils
    
    API --> BackendAPI
    Auth --> OAuth
    Checkout --> Payment
    Pages --> CDN
    Store --> BackendAPI
    Utils --> Monitoring

    style Middleware fill:#ff6b6b
    style Store fill:#4ecdc4
    style BackendAPI fill:#95e1d3
    style Auth fill:#ffd93d
    style Components fill:#a8e6cf
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant Middleware
    participant NextAuth
    participant Backend
    participant OAuth
    
    User->>Browser: Click Login
    Browser->>NextAuth: POST /api/auth/signin
    
    alt Credentials Login
        NextAuth->>Backend: POST /auth/login
        Backend-->>NextAuth: {user, tokens}
        NextAuth->>NextAuth: Create JWT Session
        NextAuth-->>Browser: Set Session Cookie
    else OAuth Login
        NextAuth->>OAuth: Redirect to Provider
        OAuth-->>User: Login Page
        User->>OAuth: Enter Credentials
        OAuth-->>NextAuth: Callback with Code
        NextAuth->>Backend: POST /auth/oauth
        Backend-->>NextAuth: {user, tokens}
        NextAuth->>NextAuth: Create JWT Session
        NextAuth-->>Browser: Set Session Cookie
    end
    
    Browser->>Browser: Store Session
    Browser-->>User: Redirect to Dashboard
    
    User->>Browser: Access Protected Route
    Browser->>Middleware: Request with Session
    Middleware->>Middleware: Verify JWT
    
    alt Valid Session
        Middleware-->>Browser: Allow Access
        Browser-->>User: Show Protected Content
    else Invalid/Expired Session
        Middleware->>NextAuth: Refresh Token
        alt Refresh Success
            NextAuth->>Backend: POST /auth/refresh
            Backend-->>NextAuth: New Access Token
            NextAuth-->>Browser: Update Session
            Browser-->>User: Show Protected Content
        else Refresh Failed
            Middleware-->>Browser: Redirect to Login
            Browser-->>User: Login Page
        end
    end
```

## Data Flow Architecture

```mermaid
graph LR
    subgraph "UI Components"
        Component[React Component]
    end
    
    subgraph "State Management"
        Query[React Query<br/>Server State]
        Zustand[Zustand<br/>Client State]
    end
    
    subgraph "API Layer"
        Service[Service Layer<br/>Business Logic]
        Client[API Client<br/>Axios + Interceptors]
    end
    
    subgraph "Backend"
        REST[REST API]
        DB[(Database)]
    end
    
    Component -->|Read Data| Query
    Component -->|Update Data| Query
    Component -->|Local State| Zustand
    
    Query -->|Fetch| Service
    Query -->|Mutate| Service
    Query -.->|Cache| Query
    
    Service -->|Transform| Client
    
    Client -->|HTTP Request| REST
    Client -.->|Retry Logic| Client
    Client -.->|Error Handler| Client
    
    REST --> DB
    REST -->|Response| Client
    Client -->|Data| Service
    Service -->|Normalized| Query
    Query -->|Render| Component
    
    style Query fill:#4ecdc4
    style Zustand fill:#95e1d3
    style Client fill:#ffd93d
    style REST fill:#ff6b6b
```

## Feature Module Structure

```mermaid
graph TB
    subgraph "Feature Module Example: Product"
        Components["📦 components/<br/>ProductCard<br/>ProductGrid<br/>ProductDetail"]
        Hooks["🪝 hooks/<br/>useProducts<br/>useProduct<br/>useInfiniteProducts"]
        Services["⚙️ services/<br/>productApi.ts<br/>productService.ts"]
        Types["📝 types/<br/>product.types.ts"]
        Schemas["✓ schemas/<br/>product.schema.ts"]
    end
    
    Components --> Hooks
    Hooks --> Services
    Hooks --> Types
    Services --> Types
    Services --> Schemas
    Components --> Types
    
    style Components fill:#a8e6cf
    style Hooks fill:#ffd93d
    style Services fill:#95e1d3
    style Types fill:#ff6b6b
    style Schemas fill:#4ecdc4
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        Dev[Developer]
        Git[GitHub Repository]
    end
    
    subgraph "CI/CD Pipeline"
        Actions[GitHub Actions]
        Build[Build & Test]
        Docker[Docker Build]
    end
    
    subgraph "Production Environment"
        CDN[Vercel/CDN]
        Edge[Edge Functions]
        Lambda[Serverless Functions]
        Static[Static Assets]
    end
    
    subgraph "External Services"
        API[Backend API]
        DB[(Database)]
        Storage[Object Storage]
        Monitor[Monitoring<br/>Sentry]
    end
    
    Dev -->|git push| Git
    Git -->|trigger| Actions
    Actions --> Build
    Build --> Docker
    Docker -->|deploy| CDN
    
    CDN --> Edge
    CDN --> Lambda
    CDN --> Static
    
    Edge --> API
    Lambda --> API
    Lambda --> Storage
    API --> DB
    
    Edge -.->|logs| Monitor
    Lambda -.->|logs| Monitor
    API -.->|logs| Monitor
    
    style Actions fill:#4ecdc4
    style CDN fill:#95e1d3
    style API fill:#ffd93d
    style Monitor fill:#ff6b6b
```

## Security Layers

```mermaid
graph TB
    Request[Incoming Request]
    
    subgraph "Security Layers"
        Layer1["🛡️ Layer 1: Edge Middleware<br/>- Rate Limiting<br/>- CSRF Protection<br/>- Security Headers"]
        Layer2["🔐 Layer 2: Authentication<br/>- JWT Verification<br/>- Session Management<br/>- Role-Based Access"]
        Layer3["✓ Layer 3: Validation<br/>- Zod Schemas<br/>- Input Sanitization<br/>- Type Checking"]
        Layer4["🔒 Layer 4: API Security<br/>- HTTPS Only<br/>- CORS Policy<br/>- API Key Validation"]
    end
    
    Response[Secure Response]
    
    Request --> Layer1
    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer3 --> Layer4
    Layer4 --> Response
    
    style Layer1 fill:#ff6b6b
    style Layer2 fill:#ffd93d
    style Layer3 fill:#4ecdc4
    style Layer4 fill:#95e1d3
```

## Key Architectural Decisions

### Why Feature-Based Architecture?

**Benefits:**
- ✅ Better code organization by business domain
- ✅ Easy to locate and modify features
- ✅ Promotes modular, reusable code
- ✅ Scalable for large teams
- ✅ Clear ownership boundaries

**Structure:**
```
features/
  auth/
    ├── components/    # UI specific to auth
    ├── hooks/         # Auth-related hooks
    ├── services/      # Auth API calls
    ├── types/         # Auth types
    └── schemas/       # Auth validation
```

### Why NextAuth v4 over v5?

**Reasons:**
- ✅ Production-stable (v5 still in beta/RC as of 2026)
- ✅ Well-documented and battle-tested
- ✅ Large community support
- ✅ Better TypeScript support
- ✅ Easier migration path

### Why React Query + Zustand?

**React Query for:**
- ✅ Server state management
- ✅ Automatic caching & revalidation
- ✅ Request deduplication
- ✅ Background refetching
- ✅ Optimistic updates

**Zustand for:**
- ✅ Client-side UI state (modals, theme, etc.)
- ✅ Simple API, no boilerplate
- ✅ TypeScript friendly
- ✅ DevTools support

### Why Axios over Fetch?

**Advantages:**
- ✅ Automatic request/response transformation
- ✅ Interceptors for auth & error handling
- ✅ Request cancellation
- ✅ Timeout support
- ✅ Retry logic with axios-retry
- ✅ Better error messages

### Why Vitest over Jest?

**Benefits:**
- ✅ Faster execution (Vite-powered)
- ✅ Better ESM support
- ✅ Native TypeScript support
- ✅ Compatible with Jest API
- ✅ Watch mode with HMR
- ✅ Modern and actively maintained
