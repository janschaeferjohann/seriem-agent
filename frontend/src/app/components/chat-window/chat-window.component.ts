import { Component, OnInit, OnDestroy, output, ViewChild, ElementRef, effect, Injector, runInInjectionContext, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { AgentService, ChatMessage, ToolCall } from '../../services/agent.service';

@Component({
  selector: 'app-chat-window',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="chat-window">
      <div class="chat-header">
        <span class="header-title">CHAT</span>
        <div class="header-actions">
          <button mat-icon-button 
                  matTooltip="Clear chat"
                  (click)="clearChat()">
            <mat-icon>delete_outline</mat-icon>
          </button>
          <button mat-icon-button 
                  matTooltip="Collapse panel"
                  (click)="collapse.emit()">
            <mat-icon>chevron_right</mat-icon>
          </button>
        </div>
      </div>
      
      <div class="chat-body" [class.empty]="agentService.messages().length === 0">
        <div class="chat-messages" #messagesContainer>
        @if (agentService.messages().length === 0) {
          <div class="empty-state">
            <div class="empty-icon">◈</div>
            <h3>Welcome to Seriem Agent</h3>
            <p>Ask me to help with coding tasks, file operations, or explore the workspace.</p>
            <div class="suggestions">
              <button class="suggestion" (click)="sendSuggestion('List all files in the workspace')">
                List all files
              </button>
              <button class="suggestion" (click)="sendSuggestion('Create a hello.py file with a simple hello world program')">
                Create hello.py
              </button>
              <button class="suggestion" (click)="sendSuggestion('What can you help me with?')">
                What can you do?
              </button>
            </div>
          </div>
        }
        
        @for (message of agentService.messages(); track $index) {
          <div class="message" [class]="message.role">
            <div class="message-avatar">
              @if (message.role === 'user') {
                <mat-icon>person</mat-icon>
              } @else {
                <span class="agent-icon">◈</span>
              }
            </div>
            <div class="message-content">
              <div class="message-header">
                <span class="message-sender">{{ message.role === 'user' ? 'You' : 'Agent' }}</span>
                <span class="message-time">{{ formatTime(message.timestamp) }}</span>
              </div>
              <div class="message-body">
                @if (message.parts && message.parts.length > 0) {
                  <div class="message-parts">
                    @for (part of message.parts; track $index) {
                      @if (part.type === 'text') {
                        @if (part.content) {
                          <div class="message-text" [innerHTML]="formatContent(part.content)"></div>
                        }
                      } @else if (part.type === 'tool_call') {
                        <div class="tool-call" [class.subagent-tool]="isSubagentTool(part.toolCall.name)">
                          <div class="tool-top">
                            <div class="tool-header">
                              <mat-icon>{{ isSubagentTool(part.toolCall.name) ? 'smart_toy' : 'build' }}</mat-icon>
                              <span class="tool-name">{{ part.toolCall.name }}</span>
                              @if (isSubagentTool(part.toolCall.name)) {
                                <span class="tool-badge">Subagent</span>
                              }
                            </div>
                            @if (part.toolCall.result) {
                              <button
                                mat-icon-button
                                class="tool-toggle"
                                [matTooltip]="isToolResultExpanded(part.toolCall) ? 'Hide result' : 'Show result'"
                                (click)="toggleToolResult(part.toolCall, $event)">
                                <mat-icon>{{ isToolResultExpanded(part.toolCall) ? 'expand_less' : 'expand_more' }}</mat-icon>
                              </button>
                            }
                          </div>
                          @if (part.toolCall.args) {
                            <pre class="tool-args">{{ formatArgs(part.toolCall.args) }}</pre>
                          }
                          @if (part.toolCall.result) {
                            @if (isToolResultExpanded(part.toolCall)) {
                              <div class="tool-result">
                                <span class="result-label">Result:</span>
                                <pre class="result-content">{{ part.toolCall.result }}</pre>
                              </div>
                            } @else {
                              <div class="tool-result tool-result-collapsed">
                                <span class="result-label">Result:</span>
                                <span class="result-collapsed-text">Hidden</span>
                              </div>
                            }
                          }
                        </div>
                      }
                    }
                  </div>
                } @else {
                  @if (message.content) {
                    <div class="message-text" [innerHTML]="formatContent(message.content)"></div>
                  }
                  @if (message.toolCalls && message.toolCalls.length > 0) {
                    <div class="tool-calls">
                      @for (toolCall of message.toolCalls; track $index) {
                        <div class="tool-call" [class.subagent-tool]="isSubagentTool(toolCall.name)">
                          <div class="tool-top">
                            <div class="tool-header">
                              <mat-icon>{{ isSubagentTool(toolCall.name) ? 'smart_toy' : 'build' }}</mat-icon>
                              <span class="tool-name">{{ toolCall.name }}</span>
                              @if (isSubagentTool(toolCall.name)) {
                                <span class="tool-badge">Subagent</span>
                              }
                            </div>
                            @if (toolCall.result) {
                              <button
                                mat-icon-button
                                class="tool-toggle"
                                [matTooltip]="isToolResultExpanded(toolCall) ? 'Hide result' : 'Show result'"
                                (click)="toggleToolResult(toolCall, $event)">
                                <mat-icon>{{ isToolResultExpanded(toolCall) ? 'expand_less' : 'expand_more' }}</mat-icon>
                              </button>
                            }
                          </div>
                          @if (toolCall.args) {
                            <pre class="tool-args">{{ formatArgs(toolCall.args) }}</pre>
                          }
                          @if (toolCall.result) {
                            @if (isToolResultExpanded(toolCall)) {
                              <div class="tool-result">
                                <span class="result-label">Result:</span>
                                <pre class="result-content">{{ toolCall.result }}</pre>
                              </div>
                            } @else {
                              <div class="tool-result tool-result-collapsed">
                                <span class="result-label">Result:</span>
                                <span class="result-collapsed-text">Hidden</span>
                              </div>
                            }
                          }
                        </div>
                      }
                    </div>
                  }
                }
                @if (message.isStreaming) {
                  <span class="streaming-indicator">●</span>
                }
              </div>
            </div>
          </div>
        }
        <div #scrollAnchor class="scroll-anchor"></div>
      </div>
      
      <div class="chat-input">
        @if (agentService.error()) {
          <div class="error-banner">
            <mat-icon>error_outline</mat-icon>
            <span>{{ agentService.error() }}</span>
          </div>
        }
        
        <div class="input-wrapper">
          <textarea
            #inputField
            [(ngModel)]="inputMessage"
            (keydown.enter)="onEnterKey($event)"
            placeholder="Ask the agent..."
            [disabled]="agentService.isProcessing()"
            rows="1"
          ></textarea>
          <button mat-icon-button 
                  color="primary"
                  (click)="sendMessage()"
                  [disabled]="!inputMessage.trim() || agentService.isProcessing()">
            @if (agentService.isProcessing()) {
              <mat-spinner diameter="20"></mat-spinner>
            } @else {
              <mat-icon>send</mat-icon>
            }
          </button>
        </div>
      </div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      height: 100%;
    }
    
    .chat-window {
      display: flex;
      flex-direction: column;
      height: 100%;
      background: var(--bg-primary);
    }
    
    .chat-body {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-height: 0;
      
      &.empty {
        justify-content: center;
        
        .chat-messages {
          flex: 0 0 auto;
          overflow: visible;
        }
        
        .chat-input {
          margin-top: var(--spacing-lg);
        }
      }
    }
    
    .chat-header {
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 6px var(--spacing-md);
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border-default);
      height: 36px;
    }
    
    .header-title {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-secondary);
    }
    
    .header-actions {
      display: flex;
      align-items: center;
      gap: 2px;
      
      button {
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
        
        mat-icon {
          font-size: 16px;
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
      }
    }
    
    .chat-messages {
      flex: 1 1 auto;
      overflow-y: scroll;
      overflow-x: hidden;
      padding: var(--spacing-md);
      padding-right: 4px;
      min-height: 0;
      display: flex;
      flex-direction: column;
      
      /* Custom scrollbar */
      &::-webkit-scrollbar {
        width: 10px;
        display: block;
      }
      
      &::-webkit-scrollbar-track {
        background: var(--bg-tertiary);
      }
      
      &::-webkit-scrollbar-thumb {
        background: var(--kw-darkgrey);
        border-radius: 5px;
        
        &:hover {
          background: var(--kw-red);
        }
      }
      
      /* Firefox scrollbar */
      scrollbar-width: thin;
      scrollbar-color: var(--kw-darkgrey) var(--bg-tertiary);
    }
    
    .chat-messages > * {
      margin-bottom: var(--spacing-md);
    }
    
    .scroll-anchor {
      height: 1px;
      width: 100%;
    }
    
    
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      text-align: center;
      color: var(--text-secondary);
      
      .empty-icon {
        font-size: 48px;
        color: var(--accent-primary);
        margin-bottom: var(--spacing-md);
      }
      
      h3 {
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: var(--spacing-sm);
      }
      
      p {
        font-size: 14px;
        max-width: 400px;
        margin-bottom: var(--spacing-lg);
      }
    }
    
    .suggestions {
      display: flex;
      flex-wrap: wrap;
      gap: var(--spacing-sm);
      justify-content: center;
    }
    
    .suggestion {
      padding: var(--spacing-sm) var(--spacing-md);
      background: var(--bg-tertiary);
      border: 1px solid var(--border-default);
      border-radius: var(--radius-md);
      color: var(--text-primary);
      font-size: 13px;
      cursor: pointer;
      transition: all var(--transition-fast);
      
      &:hover {
        background: var(--bg-hover);
        border-color: var(--accent-primary);
      }
    }
    
    .message {
      display: flex;
      gap: var(--spacing-sm);
      
      &.user {
        .message-avatar {
          background: var(--chat-user-bg);
        }
      }
      
      &.assistant {
        .message-avatar {
          background: var(--bg-tertiary);
        }
      }
    }
    
    .message-avatar {
      width: 32px;
      height: 32px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      
      mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }
      
      .agent-icon {
        font-size: 16px;
        color: var(--accent-primary);
      }
    }
    
    .message-content {
      flex: 1;
      min-width: 0;
    }
    
    .message-header {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      margin-bottom: var(--spacing-xs);
    }
    
    .message-sender {
      font-size: 13px;
      font-weight: 600;
    }
    
    .message-time {
      font-size: 11px;
      color: var(--text-muted);
    }
    
    .message-body {
      font-size: 14px;
      line-height: 1.6;
    }
    
    .message-parts {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
    }
    
    .message-text {
      word-break: break-word;
    }

    /* Styles for markdown-ish HTML generated via [innerHTML] (needs ::ng-deep) */
    :host ::ng-deep .message-text {
      h2, h3, h4 {
        margin-top: 24px;
        margin-bottom: 10px;
        font-weight: 600;
        color: var(--text-primary);
        padding-top: 8px;
      }
      
      h2 {
        font-size: 1.25rem;
        border-bottom: 1px solid var(--border-default);
        padding-bottom: 4px;
      }
      
      h3 {
        font-size: 1.1rem;
      }
      
      h4 {
        font-size: 1rem;
      }
      
      strong {
        font-weight: 600;
        color: var(--text-primary);
      }
      
      em {
        font-style: italic;
      }
      
      code {
        font-family: var(--font-mono);
        background: var(--bg-tertiary);
        padding: 2px 6px;
        border-radius: var(--radius-sm);
        font-size: 0.9em;
        color: var(--kw-red, #E30018);
      }
      
      pre {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-default);
        padding: var(--spacing-md);
        border-radius: var(--radius-md);
        overflow-x: auto;
        margin: var(--spacing-sm) 0;
        
        code {
          background: none;
          padding: 0;
          color: var(--text-primary);
          display: block;
          white-space: pre;
        }
      }
      
      ul, ol {
        margin: 8px 0;
        padding-left: 0;
        list-style: none;
      }
      
      li {
        margin: 4px 0;
        line-height: 1.6;
        padding-left: 0;
        
        &::before {
          content: "• ";
          color: var(--text-secondary);
        }
      }
      
      ol li {
        counter-increment: list-counter;
        
        &::before {
          content: counter(list-counter) ". ";
        }
      }
      
      ol {
        counter-reset: list-counter;
      }
      
      br {
        display: block;
        content: "";
        margin-top: 0.25em;
      }
    }
    
    .streaming-indicator {
      display: inline-block;
      color: var(--accent-primary);
      animation: blink 1s infinite;
    }
    
    @keyframes blink {
      0%, 50% { opacity: 1; }
      51%, 100% { opacity: 0; }
    }
    
    .tool-calls {
      margin-top: var(--spacing-sm);
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
    }
    
    .tool-call {
      background: var(--bg-secondary);
      border: 1px solid var(--border-default);
      border-radius: var(--radius-md);
      padding: var(--spacing-sm);
      font-size: 12px;
      position: relative;
    }

    .tool-call.subagent-tool {
      border-left: 3px solid var(--accent-secondary);
    }
    
    .tool-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--spacing-xs);
      margin-bottom: var(--spacing-xs);
    }
    
    .tool-header {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      color: var(--accent-primary);
      margin-bottom: 0;
      
      mat-icon {
        font-size: 14px;
        width: 14px;
        height: 14px;
      }
    }

    .tool-call.subagent-tool .tool-header {
      color: var(--accent-secondary);
    }

    .tool-badge {
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      padding: 1px 6px;
      border-radius: 999px;
      background: rgba(81, 165, 86, 0.15);
      color: var(--accent-secondary);
      border: 1px solid rgba(81, 165, 86, 0.35);
    }
    
    .tool-toggle {
      width: 22px;
      height: 22px;
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      
      mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }
    }
    
    .tool-name {
      font-family: var(--font-mono);
      font-weight: 500;
    }
    
    .tool-args, .result-content {
      font-family: var(--font-mono);
      font-size: 11px;
      background: var(--bg-tertiary);
      padding: var(--spacing-xs) var(--spacing-sm);
      border-radius: var(--radius-sm);
      overflow-x: auto;
      margin: 0;
      white-space: pre-wrap;
      word-break: break-all;
    }
    
    .tool-result {
      margin-top: var(--spacing-xs);
      
      .result-label {
        font-size: 11px;
        color: var(--text-muted);
        display: block;
        margin-bottom: var(--spacing-xs);
      }
    }
    
    .tool-result-collapsed {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      
      .result-label {
        display: inline;
        margin: 0;
      }
    }
    
    .result-collapsed-text {
      font-size: 11px;
      color: var(--text-muted);
      font-style: italic;
    }
    
    .chat-input {
      flex-shrink: 0;
      padding: var(--spacing-md);
      background: var(--bg-secondary);
      border-top: 1px solid var(--border-default);
    }
    
    .error-banner {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm) var(--spacing-md);
      background: rgba(248, 81, 73, 0.1);
      border: 1px solid var(--accent-error);
      border-radius: var(--radius-md);
      color: var(--accent-error);
      font-size: 12px;
      margin-bottom: var(--spacing-sm);
      
      mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
    }
    
    .input-wrapper {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      background: var(--bg-tertiary);
      border: 1px solid var(--border-default);
      border-radius: var(--radius-md);
      padding: var(--spacing-sm);
      
      &:focus-within {
        border-color: var(--accent-primary);
      }
      
      textarea {
        flex: 1;
        background: none;
        border: none;
        outline: none;
        color: var(--text-primary);
        font-family: var(--font-sans);
        font-size: 14px;
        line-height: 1.5;
        resize: none;
        min-height: 24px;
        max-height: 120px;
        
        &::placeholder {
          color: var(--text-muted);
        }
        
        &:disabled {
          opacity: 0.5;
        }
      }
      
      button {
        flex-shrink: 0;
      }
    }
  `]
})
export class ChatWindowComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;
  @ViewChild('scrollAnchor') private scrollAnchor!: ElementRef;
  @ViewChild('inputField') private inputField!: ElementRef<HTMLTextAreaElement>;
  
  connectionChange = output<boolean>();
  collapse = output<void>();
  
  inputMessage = '';
  private connectionInterval: ReturnType<typeof setInterval> | null = null;
  
  constructor(
    public agentService: AgentService,
    private injector: Injector
  ) {}
  
  ngOnInit(): void {
    this.agentService.connect();
    
    // Watch connection status
    this.connectionInterval = setInterval(() => {
      this.connectionChange.emit(this.agentService.isConnected());
    }, 1000);
  }
  
  ngAfterViewInit(): void {
    // Auto-scroll when messages change - must run after view is ready
    runInInjectionContext(this.injector, () => {
      effect(() => {
        const messages = this.agentService.messages();
        if (messages.length > 0) {
          // Multiple scroll attempts to handle async rendering
          this.scrollToBottom();
          setTimeout(() => this.scrollToBottom(), 100);
          setTimeout(() => this.scrollToBottom(), 300);
        }
      });
    });
    
    // Also scroll during processing with interval
    runInInjectionContext(this.injector, () => {
      effect(() => {
        const isProcessing = this.agentService.isProcessing();
        if (isProcessing) {
          const scrollInterval = setInterval(() => {
            this.scrollToBottom();
            if (!this.agentService.isProcessing()) {
              clearInterval(scrollInterval);
            }
          }, 200);
        }
      });
    });
  }
  
  ngOnDestroy(): void {
    this.agentService.disconnect();
    if (this.connectionInterval) {
      clearInterval(this.connectionInterval);
    }
  }
  
  sendMessage(): void {
    const message = this.inputMessage.trim();
    if (!message || this.agentService.isProcessing()) return;
    
    this.agentService.sendMessage(message);
    this.inputMessage = '';
    
    // Reset textarea height
    if (this.inputField) {
      this.inputField.nativeElement.style.height = 'auto';
    }
  }
  
  sendSuggestion(text: string): void {
    this.inputMessage = text;
    this.sendMessage();
  }
  
  onEnterKey(event: Event): void {
    const keyEvent = event as KeyboardEvent;
    if (!keyEvent.shiftKey) {
      keyEvent.preventDefault();
      this.sendMessage();
    }
  }
  
  clearChat(): void {
    this.agentService.clearMessages();
  }
  
  formatTime(date: Date): string {
    return new Date(date).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }
  
  formatContent(content: string): string {
    // Improved markdown formatting
    let html = content;
    
    // Escape HTML first (but preserve our markdown)
    html = html
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    
    // Code blocks (must be first to avoid other replacements inside)
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
      const langClass = lang ? ` class="language-${lang}"` : '';
      return `<pre><code${langClass}>${code.trim()}</code></pre>`;
    });
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Headers (## Header)
    html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');
    
    // Bold (**text** or __text__)
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');
    
    // Italic (*text* or _text_) - be careful not to match inside words
    html = html.replace(/(?<![*\w])\*([^*]+)\*(?![*\w])/g, '<em>$1</em>');
    html = html.replace(/(?<![_\w])_([^_]+)_(?![_\w])/g, '<em>$1</em>');
    
    // Unordered lists (- item)
    html = html.replace(/^(\s*)- (.+)$/gm, '$1<li>$2</li>');
    // Wrap consecutive <li> in <ul>
    html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');
    
    // Numbered lists (1. item)
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
    
    // Line breaks (but not inside pre/code blocks)
    // First, protect pre blocks
    const preBlocks: string[] = [];
    html = html.replace(/<pre>[\s\S]*?<\/pre>/g, (match) => {
      preBlocks.push(match);
      return `__PRE_BLOCK_${preBlocks.length - 1}__`;
    });
    
    // Add line breaks
    html = html.replace(/\n/g, '<br>');
    
    // Restore pre blocks
    preBlocks.forEach((block, i) => {
      html = html.replace(`__PRE_BLOCK_${i}__`, block);
    });
    
    // Clean up extra <br> after block elements
    html = html.replace(/<\/(h[234]|pre|ul|ol|li)><br>/g, '</$1>');
    html = html.replace(/<br><(h[234]|pre|ul|ol)/g, '<$1');
    
    return html;
  }
  
  formatArgs(args: Record<string, unknown>): string {
    return JSON.stringify(args, null, 2);
  }

  isSubagentTool(toolName: string | undefined | null): boolean {
    if (!toolName) return false;
    return (
      toolName === 'generate_datamodel' ||
      toolName === 'generate_testcase_from_datamodel' ||
      toolName === 'modify_testcase_xml'
    );
  }

  private readonly toolResultExpanded = new WeakMap<ToolCall, boolean>();

  isToolResultExpanded(toolCall: ToolCall): boolean {
    return this.toolResultExpanded.get(toolCall) ?? false;
  }

  toggleToolResult(toolCall: ToolCall, event?: Event): void {
    event?.stopPropagation();
    this.toolResultExpanded.set(toolCall, !this.isToolResultExpanded(toolCall));
  }
  
  private scrollToBottom(): void {
    try {
      // Try scrollAnchor first
      if (this.scrollAnchor?.nativeElement) {
        this.scrollAnchor.nativeElement.scrollIntoView({ behavior: 'auto', block: 'end' });
        return;
      }
      
      // Fallback to container scrollTop
      if (this.messagesContainer?.nativeElement) {
        const el = this.messagesContainer.nativeElement;
        el.scrollTop = el.scrollHeight;
      }
    } catch (e) {
      console.error('Scroll error:', e);
    }
  }
}

