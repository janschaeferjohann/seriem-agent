import { Injectable } from '@angular/core';

import { setupMonacoEnvironment } from '../monaco/monaco-environment';

@Injectable({
  providedIn: 'root',
})
export class MonacoLoaderService {
  private monacoPromise: Promise<typeof import('monaco-editor/esm/vs/editor/editor.api')> | null = null;
  private languagesRegistered = false;

  load(): Promise<typeof import('monaco-editor/esm/vs/editor/editor.api')> {
    if (this.monacoPromise) return this.monacoPromise;

    setupMonacoEnvironment();

    this.monacoPromise = (async () => {
      // Import the API-only ESM entry to avoid bundling Monaco's CSS/font assets via JS imports.
      const monaco = await import('monaco-editor/esm/vs/editor/editor.api');
      if (!this.languagesRegistered) {
        await this.registerLanguages(monaco);
        this.languagesRegistered = true;
      }
      return monaco;
    })();

    return this.monacoPromise;
  }

  private async registerLanguages(monaco: typeof import('monaco-editor/esm/vs/editor/editor.api')): Promise<void> {
    // XML syntax highlighting (Monarch tokens) - enough for read-only preview.
    const xml = await import('monaco-editor/esm/vs/basic-languages/xml/xml');

    try {
      monaco.languages.register({ id: 'xml' });
    } catch {
      // ignore duplicate register
    }

    monaco.languages.setMonarchTokensProvider('xml', xml.language);
    monaco.languages.setLanguageConfiguration('xml', xml.conf);
  }
}


