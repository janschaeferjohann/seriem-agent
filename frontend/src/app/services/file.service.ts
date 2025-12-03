import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, of } from 'rxjs';

export interface FileInfo {
  name: string;
  path: string;
  is_directory: boolean;
  size?: number;
}

export interface TreeNode extends FileInfo {
  children: TreeNode[];
  isExpanded: boolean;
  isLoading: boolean;
  level: number;
}

export interface FileListResponse {
  files: FileInfo[];
  current_path: string;
}

export interface FileContentResponse {
  path: string;
  content: string;
}

@Injectable({
  providedIn: 'root'
})
export class FileService {
  private readonly apiUrl = 'http://localhost:8000/api';
  
  // Signals for reactive state
  readonly treeNodes = signal<TreeNode[]>([]);
  readonly currentPath = signal<string>('/storage');
  readonly selectedFile = signal<FileInfo | null>(null);
  readonly fileContent = signal<string>('');
  readonly isLoading = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  
  constructor(private http: HttpClient) {}
  
  /**
   * Initialize tree with root level files
   */
  initTree(): void {
    this.isLoading.set(true);
    this.error.set(null);
    
    this.http.get<FileListResponse>(`${this.apiUrl}/files`).pipe(
      catchError(err => {
        this.error.set(err.error?.detail || 'Failed to list files');
        return of({ files: [], current_path: '/' });
      })
    ).subscribe(response => {
      const nodes = this.filesToTreeNodes(response.files, 0);
      this.treeNodes.set(nodes);
      this.currentPath.set(response.current_path);
      this.isLoading.set(false);
    });
  }
  
  /**
   * Convert FileInfo array to TreeNode array
   */
  private filesToTreeNodes(files: FileInfo[], level: number): TreeNode[] {
    return files.map(file => ({
      ...file,
      children: [],
      isExpanded: false,
      isLoading: false,
      level
    })).sort((a, b) => {
      // Directories first, then alphabetically
      if (a.is_directory && !b.is_directory) return -1;
      if (!a.is_directory && b.is_directory) return 1;
      return a.name.localeCompare(b.name);
    });
  }
  
  /**
   * Toggle expand/collapse a directory node
   */
  toggleNode(node: TreeNode): void {
    if (!node.is_directory) return;
    
    if (node.isExpanded) {
      // Collapse
      this.updateNode(node.path, { isExpanded: false });
    } else {
      // Expand - load children if not loaded
      if (node.children.length === 0) {
        this.loadChildren(node);
      } else {
        this.updateNode(node.path, { isExpanded: true });
      }
    }
  }
  
  /**
   * Load children of a directory node
   */
  private loadChildren(node: TreeNode): void {
    this.updateNode(node.path, { isLoading: true });
    
    const url = `${this.apiUrl}/files?path=${encodeURIComponent(node.path)}`;
    
    this.http.get<FileListResponse>(url).pipe(
      catchError(err => {
        this.error.set(err.error?.detail || 'Failed to load directory');
        return of({ files: [], current_path: node.path });
      })
    ).subscribe(response => {
      const children = this.filesToTreeNodes(response.files, node.level + 1);
      this.updateNode(node.path, { 
        children, 
        isExpanded: true, 
        isLoading: false 
      });
    });
  }
  
  /**
   * Update a node in the tree by path
   */
  private updateNode(path: string, updates: Partial<TreeNode>): void {
    const nodes = [...this.treeNodes()];
    this.updateNodeRecursive(nodes, path, updates);
    this.treeNodes.set(nodes);
  }
  
  private updateNodeRecursive(nodes: TreeNode[], path: string, updates: Partial<TreeNode>): boolean {
    for (let i = 0; i < nodes.length; i++) {
      if (nodes[i].path === path) {
        nodes[i] = { ...nodes[i], ...updates };
        return true;
      }
      if (nodes[i].children.length > 0) {
        const childNodes = [...nodes[i].children];
        if (this.updateNodeRecursive(childNodes, path, updates)) {
          nodes[i] = { ...nodes[i], children: childNodes };
          return true;
        }
      }
    }
    return false;
  }
  
  /**
   * Read file content
   */
  readFile(path: string): void {
    this.isLoading.set(true);
    this.error.set(null);
    
    this.http.get<FileContentResponse>(`${this.apiUrl}/files/${encodeURIComponent(path)}`).pipe(
      catchError(err => {
        this.error.set(err.error?.detail || 'Failed to read file');
        return of({ path, content: '' });
      })
    ).subscribe(response => {
      this.fileContent.set(response.content);
      this.isLoading.set(false);
    });
  }
  
  /**
   * Select a file and load its content
   */
  selectFile(file: FileInfo): void {
    if (file.is_directory) {
      this.toggleNode(file as TreeNode);
    } else {
      this.selectedFile.set(file);
      this.readFile(file.path);
    }
  }
  
  /**
   * Refresh the entire tree
   */
  refresh(): void {
    this.initTree();
  }
  
  /**
   * Get flattened visible nodes for rendering
   */
  getVisibleNodes(): TreeNode[] {
    const result: TreeNode[] = [];
    this.flattenNodes(this.treeNodes(), result);
    return result;
  }
  
  private flattenNodes(nodes: TreeNode[], result: TreeNode[]): void {
    for (const node of nodes) {
      result.push(node);
      if (node.isExpanded && node.children.length > 0) {
        this.flattenNodes(node.children, result);
      }
    }
  }
}
