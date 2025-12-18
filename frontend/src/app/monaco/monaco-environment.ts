/**
 * Configure Monaco's worker loading for bundlers that support `new URL(..., import.meta.url)`.
 *
 * Important: call this BEFORE importing `monaco-editor`.
 */
export function setupMonacoEnvironment(): void {
  const g = self as unknown as { MonacoEnvironment?: unknown };

  // Avoid re-defining if already configured.
  if ((g as any).MonacoEnvironment?.getWorker) return;

  (g as any).MonacoEnvironment = {
    getWorker: (_workerId: string, label: string) => {
      switch (label) {
        case 'json':
          return new Worker(new URL('./json.worker', import.meta.url), { type: 'module', name: 'json' });
        case 'css':
        case 'scss':
        case 'less':
          return new Worker(new URL('./css.worker', import.meta.url), { type: 'module', name: 'css' });
        case 'html':
        case 'handlebars':
        case 'razor':
          return new Worker(new URL('./html.worker', import.meta.url), { type: 'module', name: 'html' });
        case 'typescript':
        case 'javascript':
          return new Worker(new URL('./ts.worker', import.meta.url), { type: 'module', name: 'ts' });
        default:
          return new Worker(new URL('./editor.worker', import.meta.url), { type: 'module', name: 'editor' });
      }
    },
  };
}


