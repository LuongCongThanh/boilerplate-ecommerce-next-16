# 🤖 AI-Native Development with MCP (Model Context Protocol)

## 🌟 What is MCP?

**Model Context Protocol (MCP)** is an open standard that enables AI agents (like Claude, Cursor, and Antigravity) to securely connect with your local development environment. 

Instead of just "guessing" based on training data, MCP allows the AI to:
- 📂 **Browse and search** your entire codebase in real-time.
- 📚 **Fetch the latest documentation** for Next.js 16 and React 19.
- 🧪 **Run tests** and verify bug fixes automatically.
- 🧠 **Think step-by-step** through complex e-commerce logic.

---

## 🛠️ Essential MCP Servers for this Project

We have pre-configured scripts in `package.json` to help you set up these crucial servers.

### 1. Filesystem MCP (Code Awareness)
Gives the AI a Bird's-Eye view of your project structure.
- **Command**: `npm run mcp:files`
- **Use case**: "Refactor the Auth module to use the new shared component pattern."

### 2. Context7 MCP (Modern Docs)
Crucial for **Next.js 16** and **React 19**. It fetches real-time documentation, bypassing outdated AI training data.
- **Command**: `npm run mcp:context7`
- **Use case**: "How do I use the new React 19 `useOptimistic` hook for our cart updates?"

### 3. Playwright MCP (Quality Assurance)
Enables the AI to run tests and fix bugs automatically based on failures.
- **Command**: `npm run mcp:playwright`
- **Use case**: "Run the checkout E2E tests and fix the validation error in the payment step."

### 4. Sequential Thinking MCP (Reasoning)
Enhances the AI's ability to solve complex logic (e.g., promotional rules, multi-step checkout).
- **Command**: `npm run mcp:thinking`
- **Use case**: "Audit our promotional code engine and suggest improvements for edge cases."

---

## ⚙️ Configuration Guide

### For Claude Desktop
Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/thanh.luong/Documents/boilerplate-ecommerce-next-16"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

### For Cursor / Windsurf / Antigravity
Go to **Settings > IDE > MCP** and add the servers using the `npx` commands listed in the "Essential Servers" section above.

---

## 💡 AI Power-User Prompts

Combine multiple MCP capabilities for maximum efficiency:

> **"Draft a 'FlashSale' component in `@/features/marketing`. Use `Context7` to check for React 19 Server Actions best practices, and then use `Filesystem` to ensure it fits our existing atomic design system."**

> **"I'm seeing a bug in the cart state. Use `Sequential Thinking` to trace the logic from `useCart` hook to `CartStore`, and then run `Playwright` tests to verify your fix."**

---

## 🛡️ Security & Best Practices
- **Local Only**: MCP servers run locally. Your code remains private and is only accessed by the AI session you authorize.
- **Selective Access**: When using Filesystem MCP, only grant access to relevant project directories.
- **Latest Docs**: Always keep `@upstash/context7-mcp` updated to ensure the AI has access to the most recent framework changes.

---

## 📋 Roadmap for AI Integration
- [ ] Set up local Documentation RAG for instant architectural advice.
- [ ] Integrate database schema MCP to help AI write better SQL queries.
- [ ] Configure custom "Design System MCP" to enforce UI consistency.
