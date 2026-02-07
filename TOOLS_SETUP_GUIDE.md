# 🛠️ Setup Guide: Agentic Tools

This guide shows you how to complete the integration of agentic tools so the assistant can interact with ComfyUI.

## 📋 Current Status

✅ **Completed:**
- Tool folder structure created
- 4 tools implemented (addNode, removeNode, connectNodes, getWorkflowInfo)
- TypeScript definitions with Zod validation
- Implementations with error handling
- ComfyUI API helper
- Complete documentation
- Frontend configured with `useLocalRuntime`
- Backend tool calling implementation
- SSE streaming for tool calls
- Tool result handling

🔨 **Pending:**
- Test the integration end-to-end

---

## 🚀 Steps to Complete Integration

### Step 1: Update the Frontend

Replace the content of `ui/src/App.tsx` with the example code:

```bash
# Option A: Use the example file
mv ui/src/App.tsx ui/src/App.tsx.backup
mv ui/src/App.example-with-tools.tsx ui/src/App.tsx

# Option B: Edit manually
```

**Main changes:**
```typescript
// BEFORE
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";

const runtime = useChatRuntime({
  transport: new AssistantChatTransport({ api: "/api/chat" }),
});

// AFTER
import { useLocalRuntime } from "@assistant-ui/react";
import { createTools } from "@/tools";

const runtime = useLocalRuntime({
  adapter: new AssistantChatTransport({ api: "/api/chat" }),
  tools: window.app ? createTools({ app: window.app }) : {},
});
```

### Step 2: Backend Implementation ✅ (COMPLETED)

The backend has been fully implemented to support tool calling! Here's what was done:

#### 2.1. Tool Definitions Import

```python
from tools_definitions import TOOLS
```

#### 2.2. Tool Calling in Groq API

```python
stream = await client.chat.completions.create(
    model=GROQ_MODEL,
    messages=openai_messages,
    tools=TOOLS,  # Tools are passed to Groq
    stream=True,
)
```

#### 2.3. SSE Event Streaming for Tool Calls

The backend now streams three types of tool-related SSE events:

- `tool-call-start`: Emitted when a tool call begins
- `tool-call-delta`: Streams the tool arguments as they're generated
- `tool-call-end`: Emitted when the tool call is complete

#### 2.4. Message Format Conversion

The `_ui_messages_to_openai()` function now handles:
- Converting assistant messages with tool calls to OpenAI format
- Converting tool result messages from frontend to OpenAI format
- Preserving tool call IDs for proper conversation flow

#### 2.5. Documentation

See `BACKEND_TOOLS_IMPLEMENTATION.md` for detailed implementation documentation including:
- Architecture diagrams
- SSE event types
- Message format conversions
- Code flow explanation
- Testing and debugging tips

### Step 3: Rebuild the Frontend

```bash
cd ui
npm install  # Just in case
npm run build
```

### Step 4: Restart ComfyUI

```bash
# Restart ComfyUI to load backend changes
```

---

## 🧪 Testing the Integration

### Test 1: Verify tools are registered

1. Open ComfyUI
2. Open the browser console (F12)
3. Execute:
```javascript
console.log(window.app)
```
4. You should see the ComfyUI app object

### Test 2: Ask the assistant

Open the chat and try commands like:

```
"How many nodes are in my workflow?"
→ Should use getWorkflowInfo

"Add a KSampler node at position 100, 200"
→ Should use addNode

"Remove node with ID 5"
→ Should use removeNode
```

### Test 3: Verify ToolFallback UI

When the assistant uses a tool, you should see a collapsible component showing:
- Name of the tool used
- Parameters sent
- Result returned

---

## 🐛 Troubleshooting

### Problem: "window.app is undefined"

**Solution:** Tools are created conditionally. Make sure you're in the ComfyUI interface and not in standalone mode.

```typescript
// In App.tsx, verify:
tools: window.app ? createTools({ app: window.app }) : {}
```

### Problem: LLM doesn't use tools

**Possible causes:**
1. Tools aren't being sent to the backend
2. Groq doesn't support function calling with that model
3. The prompt isn't clear about which tools to use

**Solution:** 
- Verify that `tools=TOOLS` is in the Groq call
- Try a model that supports function calling (e.g., `llama3-groq-70b-8192-tool-use-preview`)
- Add a system message explaining available tools

### Problem: Error "node.connect is not a function"

**Solution:** The exact method for connecting nodes may vary. Check LiteGraph/ComfyUI documentation:

```typescript
// In implementations/connect-nodes.ts, try:
sourceNode.connect(params.sourceSlot, targetNode, params.targetSlot);
// Or:
app.graph.connectNodes(sourceNode, params.sourceSlot, targetNode, params.targetSlot);
```

### Problem: Tools execute but don't return results

**Solution:** Verify you're using the correct AI SDK protocol. The tool result must get back to the backend to continue the stream.

---

## 📚 Useful References

- **Assistant UI Docs:** https://www.assistant-ui.com/
- **AI SDK Function Calling:** https://sdk.vercel.ai/docs/ai-sdk-core/tools-and-tool-calling
- **Groq Function Calling:** https://console.groq.com/docs/tool-use
- **ComfyUI API:** https://github.com/Comfy-Org/ComfyUI_frontend

---

## 🎯 Recommended Next Steps

1. **Add more tools:**
   - `setNodeWidget`: Change widget values of a node
   - `executeWorkflow`: Execute the current workflow
   - `saveWorkflow`: Save the workflow
   - `loadWorkflow`: Load a saved workflow
   - `getNodeTypes`: Get list of available node types

2. **Improve system prompt:**
   Add a system message explaining to the LLM:
   - What tools are available
   - When to use them
   - Usage examples

3. **Implement bidirectional tool calling:**
   Allow the assistant to make multiple tool calls in sequence.

4. **Add confirmations:**
   For destructive actions (delete nodes, clear workflow), ask for user confirmation.

---

## ✅ Integration Checklist

- [ ] Frontend updated with `useLocalRuntime`
- [ ] Tools registered in the runtime
- [ ] Backend with `tools=TOOLS` in Groq call
- [ ] Backend handles tool_calls from stream
- [ ] Frontend rebuild completed
- [ ] ComfyUI restarted
- [ ] Tested with simple commands
- [ ] ToolFallback UI working
- [ ] Error handling verified

---

Need help with a specific step? Just ask! 🚀
