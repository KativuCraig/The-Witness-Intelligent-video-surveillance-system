export type IncidentType = 'VIOLENCE' | 'WEAPON' | 'THEFT';
export type IncidentStatus = 'NEW' | 'ACKNOWLEDGED' | 'RESOLVED';

export interface Incident {
  id: number;
  incident_type: IncidentType;
  confidence: number;
  status: IncidentStatus;
  detected_at: string;
  created_at: string;
  video_source: number;
  video_source_name: string;
}
