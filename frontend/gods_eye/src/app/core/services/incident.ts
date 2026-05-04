import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_URL } from '../config/api.config';
import { Incident } from '../models/incident.model';
import { unwrapList } from '../utils/api-response';

@Injectable({
  providedIn: 'root',
})
export class IncidentService {
  private readonly apiUrl = API_URL;

  constructor(private http: HttpClient) {}

  private opts(): { headers?: HttpHeaders } {
    const token = localStorage.getItem('auth_token');
    return token ? { headers: new HttpHeaders({ Authorization: `Token ${token}` }) } : {};
  }

  getIncidents(): Observable<Incident[]> {
    return this.http
      .get<Incident[] | { results: Incident[] }>(`${this.apiUrl}/incidents/`, this.opts())
      .pipe(map(unwrapList));
  }

  getIncident(id: number): Observable<Incident> {
    return this.http.get<Incident>(`${this.apiUrl}/incidents/${id}/`, this.opts());
  }

  /** Security operator confirms the linked incident (ACKNOWLEDGED). */
  confirmIncident(id: number): Observable<Incident> {
    return this.http.post<Incident>(`${this.apiUrl}/incidents/${id}/confirm/`, {}, this.opts());
  }

  /** Operator dismisses / closes the incident (RESOLVED). */
  dismissIncident(id: number): Observable<Incident> {
    return this.http.post<Incident>(`${this.apiUrl}/incidents/${id}/dismiss/`, {}, this.opts());
  }
}

