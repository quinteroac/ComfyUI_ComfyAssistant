# Text-Based Tools Testing Guide

## Implementation Status: ✅ READY FOR TESTING

All components have been implemented and the frontend has been built successfully.

## What Was Implemented

### 1. System Prompts ([agent_prompts.py](agent_prompts.py))
- Added TOOL command format instructions
- Updated example interactions to use TOOL: syntax
- LLM now knows to embed `TOOL:toolName:{params}` in responses

### 2. Tool Interceptor Hook ([ui/src/hooks/useToolInterceptor.ts](ui/src/hooks/useToolInterceptor.ts))
- Monitors assistant messages for TOOL: patterns
- Parses tool name and parameters from text
- Executes tools locally using window.app
- Appends results back to conversation
- Handles errors gracefully

### 3. App Integration ([ui/src/App.tsx](ui/src/App.tsx))
- Added useToolInterceptor hook to ChatWithTools component
- Hook runs within AssistantRuntimeProvider context
- Has access to runtime and messages

### 4. Frontend Build
- Built successfully: `dist/example_ext/App-lsfPtnIw.js` (625.74 kB)
- All TypeScript compiled without errors

---

## How to Test

### Prerequisites

1. **Environment configured:**
   ```bash
   # Verify .env exists with Groq API key
   cat .env | grep GROQ_API_KEY
   ```

2. **ComfyUI running:**
   ```bash
   # Start ComfyUI (or restart if already running)
   # The extension will load automatically
   ```

3. **Browser console open:**
   - Press F12 to open DevTools
   - Watch for `[ToolInterceptor]` log messages

---

## Test Cases

### Test 1: Basic Tool Execution - Add Node

**Steps:**
1. Open ComfyUI Assistant tab
2. Type: "Add a KSampler node"
3. Send message

**Expected Behavior:**
1. LLM responds with text containing: `TOOL:addNode:{"nodeType":"KSampler"}`
2. Console logs: `[ToolInterceptor] Detected tool call: addNode`
3. Console logs: `[ToolInterceptor] Executing addNode...`
4. KSampler node appears on canvas
5. Console logs: `[ToolInterceptor] Tool addNode result: {success: true, ...}`
6. New message appears in chat: "Tool "addNode" executed: Success. {...}"

**Success Criteria:**
- ✅ Node appears on canvas
- ✅ No console errors
- ✅ Tool result message added to chat

---

### Test 2: Get Workflow Information

**Steps:**
1. Add a few nodes manually to the canvas
2. In chat, type: "What nodes are in my workflow?"
3. Send message

**Expected Behavior:**
1. LLM responds with: `TOOL:getWorkflowInfo:{}`
2. Tool executes and returns node list
3. Result appended to chat
4. LLM receives result and summarizes the nodes

**Success Criteria:**
- ✅ Correct node list returned
- ✅ LLM uses the information in response
- ✅ Node IDs match canvas

---

### Test 3: Multiple Tool Calls

**Steps:**
1. Clear canvas (or start fresh)
2. Type: "Set up a basic text-to-image workflow"
3. Send message

**Expected Behavior:**
1. LLM responds with multiple TOOL commands:
   ```
   TOOL:addNode:{"nodeType":"CheckpointLoaderSimple"}
   TOOL:addNode:{"nodeType":"CLIPTextEncode"}
   TOOL:addNode:{"nodeType":"EmptyLatentImage"}
   TOOL:addNode:{"nodeType":"KSampler"}
   ```
2. All tools execute in sequence
3. Multiple nodes appear on canvas
4. Multiple tool results added to chat

**Success Criteria:**
- ✅ All nodes added
- ✅ Execution is sequential
- ✅ No race conditions

---

### Test 4: Tool with Position

**Steps:**
1. Type: "Add a SaveImage node at position x:500, y:300"
2. Send message

**Expected Behavior:**
1. LLM responds with: `TOOL:addNode:{"nodeType":"SaveImage","position":{"x":500,"y":300}}`
2. Node added at specified position
3. Tool result includes position

**Success Criteria:**
- ✅ Node at correct position
- ✅ Position parameter parsed correctly

---

### Test 5: Error Handling - Invalid Node Type

**Steps:**
1. Type: "Add an InvalidNodeTypeThatDoesntExist"
2. Send message

**Expected Behavior:**
1. LLM tries: `TOOL:addNode:{"nodeType":"InvalidNodeTypeThatDoesntExist"}`
2. Tool executes but fails
3. Error result: `{success: false, error: "Could not create node..."}`
4. Error message added to chat
5. LLM explains the error to user

**Success Criteria:**
- ✅ Error caught gracefully
- ✅ No console errors (except expected tool failure)
- ✅ User gets helpful error message

---

### Test 6: Connect Nodes

**Steps:**
1. Manually add 2 nodes (or use chat to add them)
2. Note their IDs (check console or canvas)
3. Type: "Connect node 1 output 0 to node 2 input 0"
4. Send message

**Expected Behavior:**
1. LLM responds with: `TOOL:connectNodes:{"sourceNodeId":1,"sourceSlot":0,"targetNodeId":2,"targetSlot":0}`
2. Connection created on canvas
3. Tool result confirms connection

**Success Criteria:**
- ✅ Connection visible on canvas
- ✅ Correct nodes connected
- ✅ Correct slots used

---

### Test 7: Remove Node

**Steps:**
1. Add a node (manually or via chat)
2. Note its ID
3. Type: "Remove node 5" (use actual ID)
4. Send message

**Expected Behavior:**
1. LLM responds with: `TOOL:removeNode:{"nodeId":5}`
2. Node disappears from canvas
3. Tool result confirms removal

**Success Criteria:**
- ✅ Node removed from canvas
- ✅ Other nodes unaffected
- ✅ No errors

---

### Test 8: Multiple Tools in Sequence

**Steps:**
1. Type: "Add a KSampler and then tell me what's in my workflow"
2. Send message

**Expected Behavior:**
1. LLM responds with:
   ```
   TOOL:addNode:{"nodeType":"KSampler"}
   TOOL:getWorkflowInfo:{}
   ```
2. Both tools execute
3. Both results added
4. LLM uses workflow info in final response

**Success Criteria:**
- ✅ Both tools execute
- ✅ Results flow back to LLM
- ✅ LLM mentions the newly added node

---

## Debugging

### Console Messages to Watch

**Successful execution:**
```
[ToolInterceptor] Detected tool call: addNode {nodeType: "KSampler"}
[ToolInterceptor] Executing addNode... {nodeType: "KSampler"}
[ToolInterceptor] Tool addNode result: {success: true, data: {...}}
```

**Failed execution:**
```
[ToolInterceptor] Detected tool call: addNode {nodeType: "Invalid"}
[ToolInterceptor] Executing addNode... {nodeType: "Invalid"}
[ToolInterceptor] Tool addNode result: {success: false, error: "..."}
```

**Parse error:**
```
[ToolInterceptor] Failed to parse tool params for addNode: ...
[ToolInterceptor] Raw JSON: {invalid json}
```

### Common Issues

**1. Tool commands not detected**
- Check LLM response contains `TOOL:` pattern
- Verify pattern matches exactly: `TOOL:toolName:{json}`
- Check console for parse errors

**2. Tools not executing**
- Verify `window.app` exists: `console.log(window.app)`
- Check if hook is being called
- Verify tools are registered: `console.log(createTools({app: window.app}))`

**3. Results not appearing in chat**
- Check `runtime.append()` is called
- Verify result format is correct
- Look for errors in console

**4. LLM not using tool results**
- Verify result message is added to conversation
- Check backend receives the result in next request
- System prompt may need adjustment

---

## Verification Checklist

Before reporting success:

- [ ] LLM generates TOOL: commands correctly
- [ ] Tool commands are detected by interceptor
- [ ] Tools execute without errors
- [ ] Results are appended to chat
- [ ] LLM receives and uses results
- [ ] Canvas updates reflect tool actions
- [ ] Error handling works properly
- [ ] Multiple tools can execute in one response
- [ ] No console errors (except expected tool failures)

---

## Manual Testing Script

```javascript
// Run in browser console to test tool execution directly

// 1. Verify window.app exists
console.log('ComfyUI app:', window.app);

// 2. Test tool creation
const tools = window.createTools ? window.createTools({app: window.app}) : null;
console.log('Tools:', tools);

// 3. Test addNode manually
if (tools?.addNode) {
  const result = await tools.addNode.execute({nodeType: 'KSampler'});
  console.log('Manual addNode result:', result);
}

// 4. Test getWorkflowInfo
if (tools?.getWorkflowInfo) {
  const result = await tools.getWorkflowInfo.execute({});
  console.log('Workflow info:', result);
}
```

---

## Next Steps After Testing

1. **If tests pass:**
   - Document any edge cases discovered
   - Create usage examples for users
   - Update CHANGELOG.md

2. **If tests fail:**
   - Check console errors
   - Verify TOOL: pattern in LLM response
   - Debug tool execution flow
   - Adjust system prompts if needed

3. **Optimization:**
   - Fine-tune system prompts based on LLM behavior
   - Add more examples if LLM struggles
   - Optimize tool result formatting
   - Add loading indicators in UI

---

## Success Metrics

- **Accuracy**: Tools execute correctly 95%+ of the time
- **Reliability**: No crashes or frozen UI
- **UX**: Results appear within 1-2 seconds
- **Clarity**: Tool results are understandable to LLM
- **Error Recovery**: Failures don't break the chat

---

## Rollback Instructions

If something goes wrong and you need to revert:

```bash
# Restore previous App.tsx
cd ui/src
mv App.tsx.backup App.tsx

# Remove tool interceptor
rm hooks/useToolInterceptor.ts

# Restore old agent_prompts.py from git
cd ../..
git checkout agent_prompts.py

# Rebuild
cd ui
npm run build
```

---

## Ready to Test!

1. Restart ComfyUI to load updated Python backend
2. Open ComfyUI in browser
3. Open Assistant tab
4. Open browser console (F12)
5. Try: "Add a KSampler node"
6. Watch the magic happen! ✨
