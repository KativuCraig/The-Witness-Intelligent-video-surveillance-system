import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_URL } from '../config/api.config';
import { Evidence } from '../models/evidence.model';
import { unwrapList } from '../utils/api-response';

@Injectable({
  providedIn: 'root',
})
export class EvidenceService {
  private readonly apiUrl = API_URL;

  constructor(private http: HttpClient) {}

  getEvidence(incidentId?: number): Observable<Evidence[]> {
    let url = `${this.apiUrl}/evidence/`;
    if (incidentId) {
      url += `?incident=${incidentId}`;
    }
    const token = localStorage.getItem('auth_token');
    const headers = token ? new HttpHeaders({ Authorization: `Token ${token}` }) : undefined;
    return this.http
      .get<Evidence[] | { results: Evidence[] }>(url, headers ? { headers } : {})
      .pipe(map(unwrapList));
  }
}

