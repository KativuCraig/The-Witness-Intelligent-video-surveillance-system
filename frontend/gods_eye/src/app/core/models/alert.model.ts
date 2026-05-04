import { IncidentStatus, IncidentType } from './incident.model';

export type DeliveryStatus = 'SENT' | 'DELIVERED' | 'FAILED';

export interface Alert {
  id: number;
  incident: number;
  incident_type: IncidentType;
  /** Incident workflow status from the backend (optional for older APIs). */
  incident_status?: IncidentStatus;
  sent_at: string;
  delivery_status: DeliveryStatus;
}
