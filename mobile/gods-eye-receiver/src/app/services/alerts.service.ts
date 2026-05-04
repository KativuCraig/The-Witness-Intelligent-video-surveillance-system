import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';

export interface AlertItem {
  id: number;
  incident: number;
  incident_type: string;
  /** Omitted on older API builds; treat as NEW. */
  incident_status?: string;
  sent_at: string;
  delivery_status: string;
}

@Injectable({ providedIn: 'root' })
export class AlertsService {
  constructor(private http: HttpClient) {}

  list(): Promise<AlertItem[]> {
    return firstValueFrom(
      this.http.get<AlertItem[]>(`${environment.apiUrl}/alerts/`)
    );
  }

  /** Operator confirms the incident (ACKNOWLEDGED). */
  confirm(incidentId: number): Promise<void> {
    return firstValueFrom(
      this.http.post<void>(
        `${environment.apiUrl}/incidents/${incidentId}/confirm/`,
        {}
      )
    );
  }

  /** Operator dismisses the incident (RESOLVED). */
  dismiss(incidentId: number): Promise<void> {
    return firstValueFrom(
      this.http.post<void>(
        `${environment.apiUrl}/incidents/${incidentId}/dismiss/`,
        {}
      )
    );
  }
}
