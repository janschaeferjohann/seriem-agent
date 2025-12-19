/**
 * Telemetry Service
 * 
 * Manages loading and displaying local telemetry data from the backend.
 */

import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { catchError, of, tap } from 'rxjs';

export interface TelemetryEvent {
  event_type: string;
  timestamp: string;
  session_id: string;
  app_version: string;
  payload: Record<string, any>;
}

export interface TelemetryStats {
  enabled: boolean;
  total_sessions: number;
  total_chat_turns: number;
  total_proposals: number;
  proposals_approved: number;
  proposals_rejected: number;
  total_errors: number;
  first_event: string | null;
  last_event: string | null;
}

export interface TelemetryEventsResponse {
  events: TelemetryEvent[];
  enabled: boolean;
}

export interface TelemetryFilesResponse {
  files: Array<{
    filename: string;
    date: string;
    size_bytes: number;
  }>;
  enabled: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class TelemetryService {
  private readonly apiUrl = 'http://localhost:8000/api/telemetry';
  
  // Reactive state signals
  readonly events = signal<TelemetryEvent[]>([]);
  readonly stats = signal<TelemetryStats | null>(null);
  readonly files = signal<TelemetryFilesResponse['files']>([]);
  readonly isLoading = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly isViewerOpen = signal<boolean>(false);
  
  constructor(private http: HttpClient) {}
  
  // ============================================================================
  // Viewer Panel State
  // ============================================================================
  
  openViewer(): void {
    this.isViewerOpen.set(true);
    this.loadStats();
    this.loadEvents();
  }
  
  closeViewer(): void {
    this.isViewerOpen.set(false);
  }
  
  toggleViewer(): void {
    if (this.isViewerOpen()) {
      this.closeViewer();
    } else {
      this.openViewer();
    }
  }
  
  // ============================================================================
  // Data Loading
  // ============================================================================
  
  /**
   * Load telemetry events with optional filters
   */
  loadEvents(eventTypes?: string[], search?: string, limit = 500): void {
    this.isLoading.set(true);
    this.error.set(null);
    
    let params = new HttpParams().set('limit', limit.toString());
    
    if (eventTypes && eventTypes.length > 0) {
      // Add each event type as a separate query param
      eventTypes.forEach(type => {
        params = params.append('event_types', type);
      });
    }
    
    if (search) {
      params = params.set('search', search);
    }
    
    this.http.get<TelemetryEventsResponse>(`${this.apiUrl}/events`, { params })
      .pipe(
        tap(response => {
          this.events.set(response.events);
          this.isLoading.set(false);
        }),
        catchError(err => {
          console.error('Failed to load telemetry events:', err);
          this.error.set('Failed to load telemetry events');
          this.isLoading.set(false);
          return of({ events: [], enabled: false });
        })
      )
      .subscribe();
  }
  
  /**
   * Load telemetry statistics
   */
  loadStats(): void {
    this.http.get<TelemetryStats>(`${this.apiUrl}/stats`)
      .pipe(
        tap(stats => {
          this.stats.set(stats);
        }),
        catchError(err => {
          console.error('Failed to load telemetry stats:', err);
          this.stats.set(null);
          return of(null);
        })
      )
      .subscribe();
  }
  
  /**
   * Load list of telemetry files
   */
  loadFiles(): void {
    this.http.get<TelemetryFilesResponse>(`${this.apiUrl}/files`)
      .pipe(
        tap(response => {
          this.files.set(response.files);
        }),
        catchError(err => {
          console.error('Failed to load telemetry files:', err);
          this.files.set([]);
          return of({ files: [], enabled: false });
        })
      )
      .subscribe();
  }
  
  /**
   * Export telemetry events as JSONL file
   */
  exportEvents(startDate?: Date, endDate?: Date): void {
    let url = `${this.apiUrl}/export`;
    const params: string[] = [];
    
    if (startDate) {
      params.push(`start_date=${startDate.toISOString()}`);
    }
    if (endDate) {
      params.push(`end_date=${endDate.toISOString()}`);
    }
    
    if (params.length > 0) {
      url += '?' + params.join('&');
    }
    
    // Open download in new tab
    window.open(url, '_blank');
  }
  
  /**
   * Enable or disable telemetry collection
   */
  setEnabled(enabled: boolean): void {
    this.http.post<{ enabled: boolean }>(`${this.apiUrl}/enabled`, null, {
      params: { enabled: enabled.toString() }
    })
      .pipe(
        tap(response => {
          // Reload stats to reflect new state
          this.loadStats();
        }),
        catchError(err => {
          console.error('Failed to set telemetry enabled state:', err);
          return of({ enabled: false });
        })
      )
      .subscribe();
  }
  
  /**
   * Clear old telemetry data
   */
  clearOldEvents(beforeDate: Date): void {
    this.http.delete<{ deleted_files: number }>(`${this.apiUrl}/events`, {
      params: { before_date: beforeDate.toISOString() }
    })
      .pipe(
        tap(response => {
          console.log(`Deleted ${response.deleted_files} telemetry files`);
          // Reload data
          this.loadStats();
          this.loadEvents();
        }),
        catchError(err => {
          console.error('Failed to clear telemetry events:', err);
          return of({ deleted_files: 0 });
        })
      )
      .subscribe();
  }
}

