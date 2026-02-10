# Quick Start Guide - ComfyUI Assistant with Tools

## Ready to Use! 🚀

The text-based tool calling system is fully implemented and ready to test.

---

## Prerequisites

1. **Groq API Key configured in `.env`:**
   ```bash
   GROQ_API_KEY=your_api_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   ```

2. **Frontend built:**
   ```bash
   cd ui
   npm run build  # ✅ Already done!
   ```

---

## Start Using

### 1. Restart ComfyUI

```bash
# Restart ComfyUI to load the updated Python backend
# The extension loads automatically
```

### 2. Open the Assistant

1. Launch ComfyUI in your browser
2. Find "ComfyUI Assistant" tab in the bottom panel
3. Click to open the chat interface

### 3. Try It Out!

**Basic commands to test:**

```
Add a KSampler node
```

```
What nodes are in my workflow?
```

```
Add a CheckpointLoaderSimple at position 100, 100
```

```
Create a basic text-to-image workflow
```

---

## What to Expect

### When You Send a Message:

1. **LLM responds with text AND tool commands:**
   ```
   "I'll add a KSampler node to your workflow.
   
   TOOL:addNode:{"nodeType":"KSampler"}
   
   The node will appear on your canvas."
   ```

2. **Tool executes automatically:**
   - No button to click
   - Happens in background
   - Node appears on canvas instantly

3. **Result appears in chat:**
   ```
   Tool "addNode" executed: Success. {"nodeId":5,"nodeType":"KSampler","position":[100,100]}
   ```

4. **LLM continues with context:**
   ```
   "Done! I've added KSampler node (ID: 5) at the default position."
   ```

---

## Debugging

### Open Browser Console (F12)

Watch for these messages:

**Success:**
```
[ToolInterceptor] Detected tool call: addNode {nodeType: "KSampler"}
[ToolInterceptor] Executing addNode...
[ToolInterceptor] Tool addNode result: {success: true, data: {...}}
```

**If Nothing Happens:**

1. **Check window.app exists:**
   ```javascript
   console.log(window.app)  // Should show ComfyUI object
   ```

2. **Check tools are registered:**
   ```javascript
   // This should be available globally after build
   console.log(window.app.graph)
   ```

3. **Check for errors:**
   - Look for red errors in console
   - Check ComfyUI server logs (terminal)

---

## Available Tools

| Tool | Example Command | What It Does |
|------|----------------|--------------|
| `addNode` | `TOOL:addNode:{"nodeType":"KSampler"}` | Adds a node to canvas |
| `removeNode` | `TOOL:removeNode:{"nodeId":5}` | Removes node by ID |
| `connectNodes` | `TOOL:connectNodes:{"sourceNodeId":1,"sourceSlot":0,"targetNodeId":2,"targetSlot":0}` | Connects two nodes |
| `getWorkflowInfo` | `TOOL:getWorkflowInfo:{}` | Returns workflow state |

---

## Example Conversations

### Example 1: Add Single Node

**You:** Add a KSampler

**Assistant:** 
```
I'll add a KSampler node to your workflow.

TOOL:addNode:{"nodeType":"KSampler"}

The node will appear on your canvas.
```

**System:** Tool "addNode" executed: Success. {"nodeId":5,...}

**Assistant:** Done! I've added a KSampler node (ID: 5).

---

### Example 2: Build Workflow

**You:** Set up a basic text-to-image workflow

**Assistant:**
```
I'll create a basic workflow with the essential nodes.

TOOL:addNode:{"nodeType":"CheckpointLoaderSimple"}
TOOL:addNode:{"nodeType":"CLIPTextEncode"}
TOOL:addNode:{"nodeType":"EmptyLatentImage"}
TOOL:addNode:{"nodeType":"KSampler"}
TOOL:addNode:{"nodeType":"VAEDecode"}
TOOL:addNode:{"nodeType":"SaveImage"}

Creating the workflow now...
```

**System:** [Multiple tool results]

**Assistant:** All nodes have been added! Would you like me to connect them?

---

### Example 3: Get Information

**You:** What's in my workflow?

**Assistant:**
```
Let me check your current workflow.

TOOL:getWorkflowInfo:{}
```

**System:** Tool "getWorkflowInfo" executed: Success. {"nodeCount":3,"nodes":[...]}

**Assistant:** 
```
Your workflow has 3 nodes:
- Node 1: CheckpointLoaderSimple
- Node 2: KSampler  
- Node 3: SaveImage

Would you like me to add more nodes or connect these?
```

---

## Troubleshooting

### LLM Not Using Tools

**Symptom:** LLM responds but doesn't include TOOL: commands

**Solutions:**
1. Be more explicit: "Use the addNode tool to add a KSampler"
2. Check system prompt is loading (see Python verification above)
3. Try different phrasing: "Execute the addNode function"

### Tool Not Executing

**Symptom:** TOOL: command appears but nothing happens

**Solutions:**
1. Check console for `[ToolInterceptor]` messages
2. Verify window.app exists
3. Check for JavaScript errors
4. Ensure ComfyUI is fully loaded before using assistant

### Wrong Parameters

**Symptom:** Tool executes but with wrong values

**Solutions:**
1. Check JSON parsing in console logs
2. Verify parameter names match tool definitions
3. Check LLM is using correct format

---

## Performance

**Expected timing:**
- Tool detection: < 50ms
- Tool execution: < 100ms
- Result appending: < 50ms
- **Total overhead: ~200ms per tool**

This is negligible compared to LLM response time (~1-3 seconds).

---

## Next Steps

After successful testing:

1. **Use it!** Start building workflows with AI
2. **Provide feedback** on what works/doesn't work
3. **Customize** system prompts for your workflow
4. **Add more tools** if needed
5. **Share** with the ComfyUI community

---

## Support

If you encounter issues:

1. Check `.agents/skills/tools/` and `TOOLS_SETUP_GUIDE.md` for tool documentation
2. Check browser console and server logs
3. Verify all files were built correctly

---

**Everything is ready. Time to test!** ✨
