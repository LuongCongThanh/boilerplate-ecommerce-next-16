# 🤖 AI Coding with MCP (Model Context Protocol)

To maximize the potential of AI coding agents (Cursor, Claude Code, Cline, etc.) in this project, we utilize **MCP Servers**. These servers provide the AI with deep context, real-time file access, and automated testing capabilities.

## 🚀 Recommended MCP Servers

| Server | Purpose | Setup Command / URL |
|--------|---------|---------------------|
| **Filesystem** | Local file access & indexing | `npx @modelcontextprotocol/filesystem-server /path/to/project` |
| **Figma** | Design-to-code automation | `https://github.com/modelcontextprotocol/servers/tree/main/src/figma` |
| **Playwright** | AI-driven E2E testing | `npm i -D @playwright/mcp` |
| **Search (RAG)** | Index project documentation | `npx @modelcontextprotocol/server-memory` (or specialized RAG) |

---

## 🛠️ Setup Instructions

### 1. Filesystem MCP (Essential)
This allows your AI agent to read your folder structure and follow the project's architectural patterns.

**For Cursor:**
1. Open **Settings** > **MCP**.
2. Click **+ Add Server**.
3. Name: `Project Files`
4. Type: `command`
5. Command: `npx -y @modelcontextprotocol/filesystem-server /Users/thanh.luong/Documents/boilerplate-ecommerce-next-16`

### 2. Playwright MCP (Quality Assurance)
Enables the AI to run tests and fix bugs automatically based on test failures.

**For Claude Code:**
```bash
# Add to your local Claude MCP configuration
claude mcp add playwright --command "npx -y @playwright/mcp"
```

### 3. Figma MCP (Design)
If you have a Figma design file, provide the AI with the Figma API token and the file URL in your MCP configuration.

---

## 💡 How to use with AI Agents

Once configured, you can use high-level prompts like:

> "Create a new 'ProductReview' component in `@/features/product` based on the 'Review Card' frame in our Figma file. Use shadcn/ui and ensure it passes our accessibility tests."

> "Analyze our `ARCHITECTURE.md` and check if the current implementation of the `CartStore` in `src/features/cart/store` follows our shared module pattern."

---

## 🛡️ Security & Privacy
- **Local Runtime**: MCP servers run locally on your machine. Your code stays private and is only indexed for the AI session you are currently in.
- **Selective Access**: You can restrict the Filesystem MCP to specific directories if needed.

---

## 📋 Roadmap for MCP Integration
- [ ] Set up local Documentation RAG for instant architectural advice.
- [ ] Integrate database schema MCP to help AI write better SQL/ORM queries.
- [ ] Configure custom "Design System MCP" to enforce corporate branding.
