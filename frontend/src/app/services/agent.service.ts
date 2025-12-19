import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ApiConfigService } from './api-config.service';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  toolCalls?: ToolCall[];
  /**
   * Optional ordered parts for rendering interleaved text + tool calls.
   * When present, the UI should render `parts` instead of `content/toolCalls`.
   */
  parts?: ChatMessagePart[];

  /**
   * UI-only flags (not persisted): used to suppress model echo of large XML that
   * already exists as a tool result.
   */
  _hasXmlToolOutput?: boolean;
  _suppressingXmlEcho?: boolean;
}

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  result?: string;
}

export type ChatMessagePart =
  | { type: 'text'; content: string }
  | { type: 'tool_call'; toolCall: ToolCall };

export interface WebSocketMessage {
  type: 'stream' | 'tool_call' | 'tool_result' | 'done' | 'error';
  content: string | { name: string; args?: Record<string, unknown>; result?: string };
}

@Injectable({
  providedIn: 'root'
})
export class AgentService {
  private readonly apiConfig = inject(ApiConfigService);
  private ws: WebSocket | null = null;
  
  // Signals for reactive state
  readonly messages = signal<ChatMessage[]>([]);
  readonly isConnected = signal<boolean>(false);
  readonly isProcessing = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  
  constructor(private http: HttpClient) {}
  
  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }
    
    this.ws = new WebSocket(`${this.apiConfig.wsUrl}/ws/chat`);
    
    this.ws.onopen = () => {
      this.isConnected.set(true);
      this.error.set(null);
    };
    
    this.ws.onclose = () => {
      this.isConnected.set(false);
      // Attempt reconnect after 3 seconds
      setTimeout(() => this.connect(), 3000);
    };
    
    this.ws.onerror = (event) => {
      this.error.set('WebSocket connection error');
      console.error('WebSocket error:', event);
    };
    
    this.ws.onmessage = (event) => {
      this.handleMessage(event.data);
    };
  }
  
  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  /**
   * Send a message to the agent
   */
  sendMessage(content: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.error.set('Not connected to server');
      return;
    }
    
    // Add user message
    const userMessage: ChatMessage = {
      role: 'user',
      content,
      timestamp: new Date(),
    };
    
    this.messages.update(msgs => [...msgs, userMessage]);
    
    // Add placeholder for assistant response
    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
      toolCalls: [],
      parts: [],
    };
    
    this.messages.update(msgs => [...msgs, assistantMessage]);
    this.isProcessing.set(true);
    
    // Build chat history for context
    const chatHistory = this.messages()
      .filter(m => !m.isStreaming)
      .map(m => ({ role: m.role, content: m.content }));
    
    // Send message
    this.ws.send(JSON.stringify({
      type: 'message',
      content,
      chat_history: chatHistory.slice(0, -1), // Exclude current message
    }));
  }
  
  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data);

      const isXmlToolName = (name?: string) =>
        name === 'generate_datamodel' ||
        name === 'generate_testcase_from_datamodel' ||
        name === 'modify_testcase_xml';

      const looksLikeXmlStart = (text: string) =>
        /<\?xml\b|<\/[A-Za-z_]|<[A-Za-z_]|<!--|<!\[CDATA\[/.test(text);

      const hasToolInFlight = (msg: ChatMessage | undefined | null) =>
        !!msg?.toolCalls?.some(tc => !tc.result);
      
      switch (message.type) {
        case 'stream':
          // Append to current assistant message
          this.messages.update(msgs => {
            const updated = [...msgs];
            const lastMsg = updated[updated.length - 1];
            if (lastMsg?.role === 'assistant') {
              const chunk = message.content as string;

              // If a subagent/tool already produced large XML, suppress model echo of it.
              if (lastMsg._suppressingXmlEcho) {
                return updated;
              }
              if (lastMsg._hasXmlToolOutput && looksLikeXmlStart(chunk)) {
                lastMsg._suppressingXmlEcho = true;
                return updated;
              }

              // Also suppress XML-looking stream content while any tool call is in-flight.
              // This prevents nested/subagent streaming from polluting the chat body.
              if (hasToolInFlight(lastMsg) && looksLikeXmlStart(chunk)) {
                return updated;
              }

              lastMsg.content += chunk;

              // Keep ordered parts for UI rendering
              lastMsg.parts ??= [];
              const lastPart = lastMsg.parts[lastMsg.parts.length - 1];
              if (lastPart?.type === 'text') {
                lastPart.content += chunk;
              } else {
                lastMsg.parts.push({ type: 'text', content: chunk });
              }
            }
            return updated;
          });
          break;
          
        case 'tool_call':
          // Add tool call to current message
          const toolCallContent = message.content as { name: string; args?: Record<string, unknown> };
          this.messages.update(msgs => {
            const updated = [...msgs];
            const lastMsg = updated[updated.length - 1];
            if (lastMsg?.role === 'assistant' && lastMsg.toolCalls) {
              const toolCall: ToolCall = {
                name: toolCallContent.name,
                args: toolCallContent.args ?? {},
              };

              lastMsg.toolCalls.push(toolCall);

              // Insert tool call in ordered parts for UI rendering
              lastMsg.parts ??= [];
              lastMsg.parts.push({ type: 'tool_call', toolCall });
            }
            return updated;
          });
          break;
          
        case 'tool_result':
          // Update tool call with result
          const toolResultContent = message.content as { name: string; result: string };
          this.messages.update(msgs => {
            const updated = [...msgs];
            const lastMsg = updated[updated.length - 1];
            if (lastMsg?.role === 'assistant' && lastMsg.toolCalls) {
              const toolCall = lastMsg.toolCalls.find(tc => tc.name === toolResultContent.name && !tc.result);
              if (toolCall) {
                toolCall.result = toolResultContent.result;
              }

              // Mark that we have a large XML tool output so we can suppress model echo.
              if (
                isXmlToolName(toolResultContent.name) &&
                typeof toolResultContent.result === 'string' &&
                toolResultContent.result.trimStart().startsWith('<') &&
                toolResultContent.result.length >= 200
              ) {
                lastMsg._hasXmlToolOutput = true;
              }

              // Also update ordered parts (same tool call object reference when possible)
              if (lastMsg.parts) {
                const toolPart = lastMsg.parts.find(
                  p => p.type === 'tool_call' && p.toolCall.name === toolResultContent.name && !p.toolCall.result
                );
                if (toolPart && toolPart.type === 'tool_call') {
                  toolPart.toolCall.result = toolResultContent.result;
                }
              }
            }
            return updated;
          });
          break;
          
        case 'done':
          // Mark streaming complete
          this.messages.update(msgs => {
            const updated = [...msgs];
            const lastMsg = updated[updated.length - 1];
            if (lastMsg?.role === 'assistant') {
              lastMsg.isStreaming = false;
            }
            return updated;
          });
          this.isProcessing.set(false);
          break;
          
        case 'error':
          this.error.set(message.content as string);
          this.messages.update(msgs => {
            const updated = [...msgs];
            const lastMsg = updated[updated.length - 1];
            if (lastMsg?.role === 'assistant') {
              lastMsg.isStreaming = false;
              lastMsg.content = `Error: ${message.content}`;
            }
            return updated;
          });
          this.isProcessing.set(false);
          break;
      }
    } catch (err) {
      console.error('Failed to parse WebSocket message:', err);
    }
  }
  
  /**
   * Clear chat history
   */
  clearMessages(): void {
    this.messages.set([]);
  }
}



