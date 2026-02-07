/**
 * Hook to execute tool-call events from OpenAI Function Calling
 * 
 * Monitors assistant messages for tool-call parts (sent by backend via SSE),
 * executes the tools locally using window.app.
 */

import { useEffect, useRef } from 'react';
import { useThread, useThreadRuntime } from '@assistant-ui/react';
import { createTools } from '@/tools';

/**
 * Custom hook that executes tool-call events from the backend
 */
export function useToolExecutor() {
  const thread = useThread();
  const runtime = useThreadRuntime();
  const processedToolCallIds = useRef(new Set<string>());
  const toolResultsBuffer = useRef<Array<{toolCallId: string, toolName: string, result: any}>>([]); 
  const isSubmittingResults = useRef(false);
  
  useEffect(() => {
    // Check if window.app is available
    if (!window.app) {
      console.warn('[ToolExecutor] window.app is not available, tools will not execute');
      return;
    }
    
    // Create tools with ComfyUI context
    const tools = createTools({ app: window.app });
    
    const messages = thread.messages;
    const lastMessage = messages[messages.length - 1];
    
    // Only process assistant messages with tool-call or tool-input-available parts
    if (lastMessage?.role === 'assistant' && lastMessage.content) {
      const parts = Array.isArray(lastMessage.content) ? lastMessage.content : [];
      
      for (const part of parts) {
        // Check for tool-call or tool-input-available type from Data Stream Protocol
        if (typeof part === 'object' && part !== null && 'type' in part) {
          const partType = (part as any).type;
          
          // Accept both tool-call (converted by runtime) and tool-input-available (direct from stream)
          if (partType !== 'tool-call' && partType !== 'tool-input-available') {
            continue;
          }
          
          const toolCall = part as any;
          const toolCallId = toolCall.toolCallId;
          
          // Skip if already processed
          if (processedToolCallIds.current.has(toolCallId)) {
            continue;
          }
          
          const toolName = toolCall.toolName;
          // tool-input-available uses 'input' field, tool-call uses 'args' field
          const args = toolCall.args || toolCall.input || {};
          
          // CRITICAL: Only execute when args are complete
          // The tool-call part gets updated multiple times as argsText streams in
          // We need to wait until argsText shows a complete JSON object
          const argsText = toolCall.argsText || '';
          
          // Check if JSON is complete (ends with '}')
          // For tools with no params, '{}' is valid and complete
          const isCompleteJson = argsText.trim().endsWith('}');
          
          if (!isCompleteJson) {
            console.log(`[ToolExecutor] Waiting for complete args for ${toolName} (argsText: "${argsText}")`);
            continue;
          }
          
          // Mark as processed now that we have complete args
          processedToolCallIds.current.add(toolCallId);
          
          console.log(`[ToolExecutor] Tool call ready - toolName:`, toolName, `args:`, args);
          
          const tool = tools[toolName];
          if (!tool || !tool.execute) {
            console.warn(`[ToolExecutor] Unknown tool: ${toolName}`);
            continue;
          }
          
          // Execute tool asynchronously
          (async () => {
            try {
              console.log(`[ToolExecutor] Executing ${toolName}...`, args);
              
              // Cast to any to avoid TypeScript issues with Tool signature
              const result = await (tool.execute as any)(args);
              
              console.log(`[ToolExecutor] Tool ${toolName} result:`, result);
              
              // Store result in buffer
              toolResultsBuffer.current.push({
                toolCallId,
                toolName,
                result
              });
              
              if (result && typeof result === 'object') {
                if (result.success) {
                  console.log(`[ToolExecutor] Tool "${toolName}" executed successfully:`, result.data);
                } else if (result.error) {
                  console.error(`[ToolExecutor] Tool "${toolName}" failed:`, result.error);
                }
              }
              
              // Check if all tools have finished
              const allToolCallsInMessage = parts.filter(p => 
                typeof p === 'object' && p !== null && 'type' in p && 
                ((p as any).type === 'tool-call' || (p as any).type === 'tool-input-available')
              );
              
              console.log(`[ToolExecutor] Tool results: ${toolResultsBuffer.current.length}/${allToolCallsInMessage.length}`);
              
              // When all tools finish, wait 2 seconds then send results to get LLM response
              if (toolResultsBuffer.current.length === allToolCallsInMessage.length && !isSubmittingResults.current) {
                isSubmittingResults.current = true;
                
                // Wait 2 seconds to batch results and avoid rate limiting
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                const successCount = toolResultsBuffer.current.filter(tr => tr.result?.success).length;
                const errorCount = toolResultsBuffer.current.filter(tr => !tr.result?.success).length;
                
                const resultsMessage = toolResultsBuffer.current.map(tr => {
                  if (tr.result?.success) {
                    return `✓ ${tr.toolName} completado exitosamente`;
                  } else {
                    return `✗ ${tr.toolName} falló: ${tr.result?.error || 'Error desconocido'}`;
                  }
                }).join('\n');
                
                console.log('[ToolExecutor] ===== All Tools Completed =====');
                console.log(resultsMessage);
                console.log('[ToolExecutor] ==============================');
                
                // Show toast notification
                if (window.app?.extensionManager?.toast) {
                  window.app.extensionManager.toast.add({
                    severity: successCount > 0 ? 'success' : 'error',
                    summary: 'Acciones completadas',
                    detail: `${successCount} exitosas, ${errorCount} fallidas`,
                    life: 3000
                  });
                }
                
                // Send results back to get LLM final response (with delay to avoid rate limiting)
                console.log('[ToolExecutor] Sending results to LLM for final response...');
                runtime.append({
                  role: 'user',
                  content: [{ 
                    type: 'text', 
                    text: `Resultados de ejecución:\n${resultsMessage}\n\nPor favor proporciona una respuesta breve confirmando las acciones.`
                  }]
                });
                
                // Clear buffers
                toolResultsBuffer.current = [];
                isSubmittingResults.current = false;
              }
              
            } catch (error) {
              console.error(`[ToolExecutor] Error executing ${toolName}:`, error);
              
              // Store error in buffer too
              toolResultsBuffer.current.push({
                toolCallId,
                toolName,
                result: { success: false, error: String(error) }
              });
            }
          })();
        }
      }
    }
  }, [thread.messages, thread, runtime]);
}
