# Agent Testing Examples

This document provides test cases for validating the ComfyUI Assistant agent's behavior with tools.

## Test Categories

### 1. Basic Tool Usage
### 2. Multi-Step Operations
### 3. Information Gathering
### 4. Error Handling
### 5. Edge Cases
### 6. Complex Workflows

---

## 1. Basic Tool Usage

### Test 1.1: Add Single Node

**User Input:**
```
Add a KSampler node
```

**Expected Behavior:**
1. Agent explains it will add the node
2. Calls `addNode` tool with `nodeType: "KSampler"`
3. Reports success with node ID
4. Optionally suggests next steps

**Success Criteria:**
- ✅ Tool is called with correct parameters
- ✅ Agent confirms the action
- ✅ Response is clear and concise

---

### Test 1.2: Remove Node

**User Input:**
```
Remove node 5
```

**Expected Behavior:**
1. Agent may ask for confirmation (if destructive)
2. Calls `removeNode` tool with `nodeId: 5`
3. Reports success

**Success Criteria:**
- ✅ Confirmation is requested (good practice)
- ✅ Tool is called with correct ID
- ✅ Agent handles non-existent nodes gracefully

---

### Test 1.3: Get Workflow Info

**User Input:**
```
What's in my workflow?
```

**Expected Behavior:**
1. Calls `getWorkflowInfo` tool
2. Parses and summarizes the results
3. Presents information clearly (list of nodes, connections)

**Success Criteria:**
- ✅ Tool is called immediately
- ✅ Results are formatted well
- ✅ Agent provides context/suggestions

---

### Test 1.4: Connect Nodes

**User Input:**
```
Connect node 1 to node 2
```

**Expected Behavior:**
1. May call `getWorkflowInfo` first to verify nodes exist
2. Asks for clarification about which outputs/inputs (if ambiguous)
3. Calls `connectNodes` with correct parameters
4. Confirms connection

**Success Criteria:**
- ✅ Agent validates nodes exist
- ✅ Asks for clarification when needed
- ✅ Correct slots are used

---

## 2. Multi-Step Operations

### Test 2.1: Build Basic Workflow

**User Input:**
```
Set up a basic text-to-image workflow
```

**Expected Behavior:**
1. Explains the plan (what nodes will be added)
2. Adds nodes step-by-step:
   - CheckpointLoaderSimple
   - CLIPTextEncode (x2 for positive/negative)
   - EmptyLatentImage
   - KSampler
   - VAEDecode
   - SaveImage
3. Offers to connect them

**Success Criteria:**
- ✅ All necessary nodes are added
- ✅ Agent explains each step
- ✅ Logical node positioning (if positions specified)
- ✅ Offers to continue with connections

---

### Test 2.2: Complete Workflow Setup

**User Input:**
```
Create a text-to-image workflow and connect everything
```

**Expected Behavior:**
1. Adds all necessary nodes (as in Test 2.1)
2. Connects them in logical order:
   - Checkpoint → MODEL to KSampler
   - Checkpoint → CLIP to text encoders
   - Checkpoint → VAE to VAEDecode
   - Text encoders → conditioning to KSampler
   - EmptyLatent → LATENT to KSampler
   - KSampler → LATENT to VAEDecode
   - VAEDecode → IMAGE to SaveImage
3. Confirms completion
4. Explains how to use the workflow

**Success Criteria:**
- ✅ All nodes added and connected correctly
- ✅ Agent explains the workflow structure
- ✅ No broken connections

---

### Test 2.3: Modify Existing Workflow

**User Input:**
```
Replace my KSampler with KSamplerAdvanced
```

**Expected Behavior:**
1. Calls `getWorkflowInfo` to find the KSampler
2. Asks for confirmation before removing
3. Removes old sampler
4. Adds new sampler at similar position
5. Offers to reconnect inputs/outputs

**Success Criteria:**
- ✅ Workflow state checked first
- ✅ Confirmation requested
- ✅ Smooth transition suggested

---

## 3. Information Gathering

### Test 3.1: Workflow Analysis

**User Input:**
```
Is my workflow complete?
```

**Expected Behavior:**
1. Calls `getWorkflowInfo`
2. Analyzes for completeness:
   - Required nodes (checkpoint, sampler, decoder, save)
   - Proper connections
   - Missing components
3. Provides assessment
4. Suggests fixes if incomplete

**Success Criteria:**
- ✅ Thorough analysis
- ✅ Clear explanation of issues
- ✅ Actionable suggestions

---

### Test 3.2: Node Information

**User Input:**
```
What does node 3 do?
```

**Expected Behavior:**
1. Calls `getWorkflowInfo` to identify node type
2. Explains the node's purpose
3. Describes inputs/outputs
4. Suggests common usage

**Success Criteria:**
- ✅ Correct node identified
- ✅ Clear explanation
- ✅ Helpful context provided

---

### Test 3.3: Connection Query

**User Input:**
```
Show me all connections in my workflow
```

**Expected Behavior:**
1. Calls `getWorkflowInfo`
2. Lists all connections clearly
3. Formats as: "Node X (output) → Node Y (input)"

**Success Criteria:**
- ✅ All connections listed
- ✅ Clear, readable format
- ✅ Helpful if no connections exist

---

## 4. Error Handling

### Test 4.1: Invalid Node Type

**User Input:**
```
Add a NonExistentNode
```

**Expected Behavior:**
1. Attempts to add the node
2. Tool fails (node type doesn't exist)
3. Agent explains the error
4. Suggests similar valid node types

**Success Criteria:**
- ✅ Error handled gracefully
- ✅ Helpful error message
- ✅ Suggestions provided

---

### Test 4.2: Non-Existent Node ID

**User Input:**
```
Remove node 999
```

**Expected Behavior:**
1. May call `getWorkflowInfo` first to check
2. Attempts removal (or skips if checked first)
3. Explains node doesn't exist
4. Offers to show current nodes

**Success Criteria:**
- ✅ Error caught and explained
- ✅ No crash or confusion
- ✅ Helpful follow-up

---

### Test 4.3: Invalid Connection

**User Input:**
```
Connect node 1 output 99 to node 2 input 99
```

**Expected Behavior:**
1. Attempts connection
2. Tool fails (invalid slot indices)
3. Explains the issue
4. Offers to check valid slots

**Success Criteria:**
- ✅ Error explained clearly
- ✅ Agent doesn't make assumptions
- ✅ Offers to help correctly

---

## 5. Edge Cases

### Test 5.1: Empty Workflow

**User Input:**
```
What's in my workflow?
```

**Expected Behavior:**
1. Calls `getWorkflowInfo`
2. Returns empty/minimal result
3. Explains workflow is empty
4. Offers to create a starter workflow

**Success Criteria:**
- ✅ Handles empty state gracefully
- ✅ Doesn't error or confuse
- ✅ Proactive suggestion

---

### Test 5.2: Ambiguous Request

**User Input:**
```
Add a sampler
```

**Expected Behavior:**
1. Recognizes ambiguity (KSampler vs KSamplerAdvanced)
2. Asks for clarification
3. Suggests options

**Success Criteria:**
- ✅ Ambiguity detected
- ✅ Clear question asked
- ✅ Options presented

---

### Test 5.3: Vague Connection Request

**User Input:**
```
Connect the checkpoint to the sampler
```

**Expected Behavior:**
1. Calls `getWorkflowInfo` to identify nodes
2. Determines which output/input (MODEL output → model input)
3. Makes intelligent default choice or asks for confirmation
4. Performs connection

**Success Criteria:**
- ✅ Intelligent interpretation
- ✅ Correct slots chosen
- ✅ Explanation provided

---

## 6. Complex Workflows

### Test 6.1: Upscale Workflow

**User Input:**
```
Add an upscaling pipeline after my current workflow
```

**Expected Behavior:**
1. Calls `getWorkflowInfo` to understand current state
2. Identifies where to attach (after VAEDecode or SaveImage)
3. Adds upscaling nodes (ImageUpscaleWithModel, etc.)
4. Connects to existing workflow
5. Explains the addition

**Success Criteria:**
- ✅ Current workflow analyzed
- ✅ Correct insertion point
- ✅ Proper connections made

---

### Test 6.2: ControlNet Integration

**User Input:**
```
Add ControlNet support to my workflow
```

**Expected Behavior:**
1. Checks current workflow
2. Adds necessary nodes:
   - ControlNetLoader
   - ControlNetApply
   - LoadImage (for control image)
3. Integrates with existing conditioning
4. Explains usage

**Success Criteria:**
- ✅ All required nodes added
- ✅ Proper integration with existing nodes
- ✅ Clear usage instructions

---

### Test 6.3: Multiple Samplers

**User Input:**
```
Set up a two-pass sampling workflow
```

**Expected Behavior:**
1. Understands advanced concept
2. Adds two KSampler nodes
3. Connects first sampler output to second sampler input
4. Explains the two-pass concept

**Success Criteria:**
- ✅ Correct workflow structure
- ✅ Proper chaining
- ✅ Educational explanation

---

## Testing Methodology

### Manual Testing

1. Open ComfyUI with the extension installed
2. Open the assistant chat
3. Enter each test input
4. Verify behavior matches expectations
5. Check browser console for errors
6. Note any deviations

### Automated Testing

```python
# Example test script
test_cases = [
    {
        "input": "Add a KSampler node",
        "expected_tool": "addNode",
        "expected_params": {"nodeType": "KSampler"}
    },
    # ... more test cases
]

for test in test_cases:
    response = call_agent(test["input"])
    assert_tool_called(response, test["expected_tool"])
    assert_params_match(response, test["expected_params"])
```

### Evaluation Criteria

For each test, evaluate:

1. **Correctness** (3 points)
   - Did the agent use the right tools?
   - Were parameters correct?
   - Was the outcome as expected?

2. **Clarity** (2 points)
   - Was the response easy to understand?
   - Was technical terminology used correctly?

3. **Helpfulness** (2 points)
   - Did the agent provide context?
   - Were suggestions appropriate?
   - Was the user guided effectively?

4. **Error Handling** (2 points)
   - Were errors caught gracefully?
   - Were error messages helpful?
   - Were alternatives suggested?

5. **Efficiency** (1 point)
   - Minimal unnecessary tool calls?
   - Direct path to solution?

**Total: 10 points per test**

### Scoring

- 9-10: Excellent
- 7-8: Good
- 5-6: Acceptable
- 3-4: Needs improvement
- 0-2: Poor

---

## Reporting Issues

When a test fails, document:

1. **Test ID**: Which test failed
2. **Input**: Exact user input
3. **Expected**: What should have happened
4. **Actual**: What actually happened
5. **Tools Called**: Which tools were used (if any)
6. **Errors**: Any error messages
7. **Suggestions**: How to fix

### Example Issue Report

```
Test ID: 2.1
Input: "Set up a basic text-to-image workflow"
Expected: Agent adds 6 nodes step-by-step
Actual: Agent only added checkpoint and sampler
Tools Called: addNode (x2)
Errors: None
Suggestions: Update system prompt to include complete workflow template
```

---

## Next Steps

After testing:

1. **Document results** in a test report
2. **Identify patterns** in failures
3. **Update prompts** in `agent_prompts.py`
4. **Re-test** failed cases
5. **Iterate** until all tests pass

For prompt modifications, see `AGENT_PROMPTS_GUIDE.md`.
