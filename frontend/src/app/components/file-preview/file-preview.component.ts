import {
  AfterViewInit,
  Component,
  ElementRef,
  Injector,
  OnDestroy,
  ViewChild,
  effect,
  runInInjectionContext,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { FilePreviewService, OpenTab } from '../../services/file-preview.service';
import { MonacoLoaderService } from '../../services/monaco-loader.service';

import type * as monaco from 'monaco-editor/esm/vs/editor/editor.api';

@Component({
  selector: 'app-file-preview',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="file-preview">
      <div class="tabbar" role="tablist" aria-label="File preview tabs">
        @for (tab of filePreviewService.openTabs(); track tab.path) {
          <div
            class="tab"
            role="tab"
            [class.active]="tab.path === filePreviewService.activePath()"
            [attr.aria-selected]="tab.path === filePreviewService.activePath()"
            (click)="activate(tab.path)">
            <span class="tab-title" [matTooltip]="tab.path">{{ tab.name }}</span>
            <button
              mat-icon-button
              class="tab-close"
              [matTooltip]="'Close ' + tab.name"
              (click)="close(tab.path, $event)">
              <mat-icon>close</mat-icon>
            </button>
          </div>
        }
      </div>

      <div class="editor-wrap">
        <div #editorContainer class="editor"></div>

        @if (activeTab()?.isLoading) {
          <div class="overlay">
            <mat-spinner diameter="24"></mat-spinner>
          </div>
        }

        @if (activeTab()?.error) {
          <div class="overlay error">
            <mat-icon>error_outline</mat-icon>
            <span>{{ activeTab()?.error }}</span>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      height: 100%;
      min-height: 0;
    }

    .file-preview {
      display: flex;
      flex-direction: column;
      height: 100%;
      min-height: 0;
      overflow: hidden;
      background: var(--bg-primary);
    }

    .tabbar {
      display: flex;
      align-items: stretch;
      gap: 1px;
      background: var(--border-default);
      border-bottom: 1px solid var(--border-default);
      height: 36px;
      flex: 0 0 auto;
      overflow-x: auto;
      overflow-y: hidden;

      /* keep scrollbar subtle */
      scrollbar-width: thin;
    }

    .tab {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 0 var(--spacing-sm);
      background: var(--bg-secondary);
      color: var(--text-secondary);
      cursor: pointer;
      user-select: none;
      min-width: 120px;
      max-width: 280px;
      flex: 0 0 auto;
      border-bottom: 2px solid transparent;

      &:hover {
        background: var(--bg-hover);
      }

      &.active {
        background: var(--bg-primary);
        color: var(--text-primary);
        border-bottom-color: var(--accent-primary);
      }
    }

    .tab-title {
      flex: 1 1 auto;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 12px;
    }

    .tab-close {
      width: 22px;
      height: 22px;
      padding: 0;
      flex: 0 0 auto;

      mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
    }

    .editor-wrap {
      position: relative;
      flex: 1 1 auto;
      min-height: 0;
      overflow: hidden;
    }

    .editor {
      position: absolute;
      inset: 0;
    }

    .overlay {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--spacing-sm);
      background: rgba(255, 255, 255, 0.6);
      backdrop-filter: blur(2px);
      font-size: 12px;
      color: var(--text-secondary);
      pointer-events: none;
    }

    .overlay.error {
      background: rgba(248, 81, 73, 0.10);
      color: var(--accent-error);

      mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
    }
  `],
})
export class FilePreviewComponent implements AfterViewInit, OnDestroy {
  @ViewChild('editorContainer') private editorContainer!: ElementRef<HTMLDivElement>;

  private monaco: typeof monaco | null = null;
  private editor: monaco.editor.IStandaloneCodeEditor | null = null;
  private readonly models = new Map<string, monaco.editor.ITextModel>();
  private readonly viewStates = new Map<string, monaco.editor.ICodeEditorViewState | null>();
  private activeModelPath: string | null = null;
  private resizeObserver: ResizeObserver | null = null;

  constructor(
    public filePreviewService: FilePreviewService,
    private monacoLoader: MonacoLoaderService,
    private injector: Injector
  ) {}

  activeTab = () => this.filePreviewService.activeTab();

  async ngAfterViewInit(): Promise<void> {
    await this.initEditor();

    runInInjectionContext(this.injector, () => {
      effect(() => {
        this.syncActiveTabToEditor();
      });
    });
  }

  ngOnDestroy(): void {
    try {
      this.resizeObserver?.disconnect();
      this.resizeObserver = null;
    } catch {
      // ignore
    }

    // Dispose editor before models
    try {
      this.editor?.dispose();
    } catch {
      // ignore
    }
    this.editor = null;

    for (const model of this.models.values()) {
      try {
        model.dispose();
      } catch {
        // ignore
      }
    }
    this.models.clear();
  }

  activate(path: string): void {
    this.filePreviewService.setActive(path);
  }

  close(path: string, event?: Event): void {
    event?.stopPropagation();
    this.filePreviewService.closeTab(path);
  }

  private async initEditor(): Promise<void> {
    const monacoApi = await this.monacoLoader.load();
    this.monaco = monacoApi;

    this.editor = monacoApi.editor.create(this.editorContainer.nativeElement, {
      value: '',
      language: 'xml',
      readOnly: true,
      domReadOnly: true,
      minimap: { enabled: false },
      scrollbar: {
        verticalScrollbarSize: 10,
        horizontalScrollbarSize: 10,
        useShadows: false,
      },
      scrollBeyondLastLine: false,
      wordWrap: 'on',
      theme: 'vs',
      automaticLayout: false,
    });

    this.resizeObserver = new ResizeObserver(() => {
      this.editor?.layout();
    });
    this.resizeObserver.observe(this.editorContainer.nativeElement);

    // Ensure first layout after DOM paint
    setTimeout(() => this.editor?.layout(), 0);
  }

  private syncActiveTabToEditor(): void {
    if (!this.monaco || !this.editor) return;

    const tab = this.filePreviewService.activeTab();
    if (!tab) {
      this.editor.setModel(null);
      this.activeModelPath = null;
      return;
    }

    // Save view state for previous model
    if (this.activeModelPath && this.activeModelPath !== tab.path) {
      this.viewStates.set(this.activeModelPath, this.editor.saveViewState());
    }

    let model = this.models.get(tab.path);
    if (!model) {
      const uri = this.monaco.Uri.parse(`inmemory://model/${encodeURIComponent(tab.path)}`);
      model = this.monaco.editor.createModel(tab.content, tab.language || 'plaintext', uri);
      this.models.set(tab.path, model);
    } else {
      // Keep model in sync with loaded content (read-only preview)
      if (model.getValue() !== tab.content) {
        model.setValue(tab.content);
      }
      if (tab.language && model.getLanguageId() !== tab.language) {
        this.monaco.editor.setModelLanguage(model, tab.language);
      }
    }

    this.editor.setModel(model);

    const viewState = this.viewStates.get(tab.path);
    if (viewState) {
      this.editor.restoreViewState(viewState);
    }

    this.activeModelPath = tab.path;

    // Layout because tab switches can happen during/after splitter drag
    this.editor.layout();
  }
}


