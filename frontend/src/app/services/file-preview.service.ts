import { Injectable, computed, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import type { FileInfo, FileContentResponse } from './file.service';

export interface OpenTab {
  path: string;
  name: string;
  language: string;
  content: string;
  isLoading: boolean;
  error: string | null;
}

@Injectable({
  providedIn: 'root',
})
export class FilePreviewService {
  private readonly apiUrl = 'http://localhost:8000/api';

  readonly openTabs = signal<OpenTab[]>([]);
  readonly activePath = signal<string | null>(null);

  readonly isPreviewOpen = computed(() => this.openTabs().length > 0);
  readonly activeTab = computed(() => {
    const path = this.activePath();
    if (!path) return null;
    return this.openTabs().find(t => t.path === path) ?? null;
  });

  constructor(private http: HttpClient) {}

  openFile(file: FileInfo): void {
    if (file.is_directory) return;

    const existing = this.openTabs().find(t => t.path === file.path);
    if (existing) {
      this.activePath.set(existing.path);
      return;
    }

    const tab: OpenTab = {
      path: file.path,
      name: file.name,
      language: this.inferLanguage(file.name),
      content: '',
      isLoading: true,
      error: null,
    };

    this.openTabs.update(tabs => [...tabs, tab]);
    this.activePath.set(tab.path);

    this.http.get<FileContentResponse>(`${this.apiUrl}/files/${encodeURIComponent(file.path)}`).subscribe({
      next: (response) => {
        this.updateTab(file.path, {
          content: response.content,
          isLoading: false,
          error: null,
        });
      },
      error: (err) => {
        const message: string =
          err?.error?.detail ||
          err?.message ||
          'Failed to read file';
        this.updateTab(file.path, {
          content: '',
          isLoading: false,
          error: message,
        });
      },
    });
  }

  setActive(path: string): void {
    if (!this.openTabs().some(t => t.path === path)) return;
    this.activePath.set(path);
  }

  closeTab(path: string): void {
    const tabs = this.openTabs();
    const idx = tabs.findIndex(t => t.path === path);
    if (idx === -1) return;

    const wasActive = this.activePath() === path;
    const nextTabs = tabs.filter(t => t.path !== path);
    this.openTabs.set(nextTabs);

    if (!wasActive) return;

    if (nextTabs.length === 0) {
      this.activePath.set(null);
      return;
    }

    // Prefer previous tab; otherwise fall back to first.
    const nextIdx = Math.max(0, idx - 1);
    this.activePath.set(nextTabs[Math.min(nextIdx, nextTabs.length - 1)].path);
  }

  private updateTab(path: string, updates: Partial<OpenTab>): void {
    this.openTabs.update(tabs =>
      tabs.map(t => (t.path === path ? { ...t, ...updates } : t))
    );
  }

  private inferLanguage(filename: string): string {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'xml':
      case 'xsd':
      case 'xslt':
        return 'xml';
      case 'json':
      case 'formio':
        return 'json';
      case 'yml':
      case 'yaml':
        return 'yaml';
      case 'ts':
        return 'typescript';
      case 'js':
        return 'javascript';
      case 'md':
        return 'markdown';
      case 'txt':
        return 'plaintext';
      default:
        return 'plaintext';
    }
  }
}


