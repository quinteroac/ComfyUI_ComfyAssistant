/**
 * Hook to intercept and execute tool commands from LLM responses
 * 
 * Monitors assistant messages for TOOL:toolName:{params} patterns,
 * executes the tools locally using window.app, and appends results
 * back to the conversation.
 */

import { useEffect, useRef } from 'react';
import { useThreadRuntime, useThread } from '@assistant-ui/react';
import { createTools } from '@/tools';
import type { ToolResult } from '@/tools/types';

// Pattern to match: TOOL:toolName:{"param":"value"}
const TOOL_PATTERN = /TOOL:(\w+):(\{[^\n]+\})/g;

interface ToolCall {
  tool: string;
  params: Record<string, unknown>;
  rawMatch: string;
}

/**
 * Custom hook that intercepts tool commands from assistant messages
 * and executes them locally
 */
export function useToolInterceptor() {
  const runtime = useThreadRuntime();
  const thread = useThread();
  const processedMessageIds = useRef(new Set<string>());
  
  useEffect(() => {
    console.log('[ToolInterceptor] Hook effect triggered, messages count:', thread.messages.length);
    
    // Check if window.app is available
    if (!window.app) {
      console.warn('[ToolInterceptor] window.app is not available, tools will not execute');
      return;
    }
    
    console.log('[ToolInterceptor] window.app is available:', !!window.app);
    
    // Create tools with ComfyUI context
    const tools = createTools({ app: window.app });
    console.log('[ToolInterceptor] Tools created:', Object.keys(tools));
    
    const messages = thread.messages;
    const lastMessage = messages[messages.length - 1];
    
    console.log('[ToolInterceptor] Last message:', {
      role: lastMessage?.role,
      id: lastMessage?.id,
      hasContent: !!lastMessage?.content
    });
    
    // Only process assistant messages that haven't been processed yet
    if (lastMessage?.role === 'assistant' && lastMessage.id) {
      if (processedMessageIds.current.has(lastMessage.id)) {
        console.log('[ToolInterceptor] Message already processed:', lastMessage.id);
        return; // Already processed
      }
      
      // Extract text content from message
      const content = extractTextContent(lastMessage);
      console.log('[ToolInterceptor] Extracted content:', content);
      
      if (!content) {
        console.log('[ToolInterceptor] No content extracted');
        return;
      }
      
      // Parse tool calls from content
      const toolCalls = parseToolCalls(content);
      console.log('[ToolInterceptor] Parsed tool calls:', toolCalls.length);
      
      if (toolCalls.length > 0) {
        // Mark as processed
        processedMessageIds.current.add(lastMessage.id);
        console.log('[ToolInterceptor] Marked message as processed:', lastMessage.id);
        
        // Execute tools
        executeToolCalls(toolCalls, tools, runtime);
      } else {
        console.log('[ToolInterceptor] No tool calls found in message');
      }
    }
  }, [thread.messages, runtime, thread]);
}

/**
 * Extract text content from a message
 */
function extractTextContent(message: any): string {
  if (typeof message.content === 'string') {
    return message.content;
  }
  
  if (Array.isArray(message.content)) {
    // Join with empty string (no separator) since streaming already includes spaces
    const text = message.content
      .filter((part: any) => part.type === 'text')
      .map((part: any) => part.text)
      .join('');
    
    return text;
  }
  
  return '';
}

/**
 * Parse TOOL:name:{params} patterns from text
 */
function parseToolCalls(text: string): ToolCall[] {
  const calls: ToolCall[] = [];
  
  console.log('[ToolInterceptor] Parsing text length:', text.length);
  console.log('[ToolInterceptor] Text contains TOOL:', text.includes('TOOL:'));
  console.log('[ToolInterceptor] Full text for regex:', JSON.stringify(text.substring(0, 500)));
  
  // Reset regex state
  TOOL_PATTERN.lastIndex = 0;
  
  let match;
  while ((match = TOOL_PATTERN.exec(text)) !== null) {
    const [rawMatch, tool, paramsJson] = match;
    
    console.log(`[ToolInterceptor] Regex matched! Tool: ${tool}, JSON: ${paramsJson}`);
    
    try {
      const params = JSON.parse(paramsJson);
      calls.push({ tool, params, rawMatch });
      
      console.log(`[ToolInterceptor] Detected tool call: ${tool}`, params);
    } catch (e) {
      console.error(`[ToolInterceptor] Failed to parse tool params for ${tool}:`, e);
      console.error(`[ToolInterceptor] Raw JSON: ${paramsJson}`);
    }
  }
  
  console.log('[ToolInterceptor] Total matches found:', calls.length);
  
  return calls;
}

/**
 * Execute tool calls and append results to the conversation
 */
async function executeToolCalls(
  toolCalls: ToolCall[],
  tools: Record<string, any>,
  runtime: any
) {
  for (const { tool, params } of toolCalls) {
    if (!tools[tool]) {
      console.warn(`[ToolInterceptor] Unknown tool: ${tool}`);
      
      // Append error result
      runtime.append({
        role: 'user',
        content: `Tool execution failed: Unknown tool "${tool}"`
      });
      continue;
    }
    
    try {
      console.log(`[ToolInterceptor] Executing ${tool}...`, params);
      
      // Execute the tool
      const result: ToolResult = await tools[tool].execute(params);
      
      console.log(`[ToolInterceptor] Tool ${tool} result:`, result);
      
      // Log result (don't append to chat to avoid message duplication errors)
      if (result.success) {
        console.log(`[ToolInterceptor] Tool "${tool}" executed successfully:`, result.data);
      } else {
        console.error(`[ToolInterceptor] Tool "${tool}" failed:`, result.error);
      }
      
    } catch (error) {
      console.error(`[ToolInterceptor] Error executing ${tool}:`, error);
      
      // Append error result
      runtime.append({
        role: 'user',
        content: `Tool execution error: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    }
  }
}
