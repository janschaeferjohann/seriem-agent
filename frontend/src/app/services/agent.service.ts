import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  toolCalls?: ToolCall[];
}

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  result?: string;
}

export interface WebSocketMessage {
  type: 'stream' | 'tool_call' | 'tool_result' | 'done' | 'error';
  content: string | { name: string; args?: Record<string, unknown>; result?: string };
}

@Injectable({
  providedIn: 'root'
})
export class AgentService {
  private readonly wsUrl = 'ws://localhost:8000/ws/chat';
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
    
    this.ws = new WebSocket(this.wsUrl);
    
    this.ws.onopen = () => {
      this.isConnected.set(true);
      this.error.set(null);
      console.log('WebSocket connected');
    };
    
    this.ws.onclose = () => {
      this.isConnected.set(false);
      console.log('WebSocket disconnected');
      
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
      
      switch (message.type) {
        case 'stream':
          // Append to current assistant message
          this.messages.update(msgs => {
            const updated = [...msgs];
            const lastMsg = updated[updated.length - 1];
            if (lastMsg?.role === 'assistant') {
              lastMsg.content += message.content as string;
            }
            return updated;
          });
          break;
          
        case 'tool_call':
          // Add tool call to current message
          const toolCallContent = message.content as { name: string; args: Record<string, unknown> };
          this.messages.update(msgs => {
            const updated = [...msgs];
            const lastMsg = updated[updated.length - 1];
            if (lastMsg?.role === 'assistant' && lastMsg.toolCalls) {
              lastMsg.toolCalls.push({
                name: toolCallContent.name,
                args: toolCallContent.args,
              });
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

