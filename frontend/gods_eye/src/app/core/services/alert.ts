import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_URL } from '../config/api.config';
import { Alert } from '../models/alert.model';
import { unwrapList } from '../utils/api-response';

@Injectable({
  providedIn: 'root',
})
export class AlertService {
  private readonly apiUrl = API_URL;

  constructor(private http: HttpClient) {}

  getAlerts(): Observable<Alert[]> {
    return this.http
      .get<Alert[] | { results: Alert[] }>(`${this.apiUrl}/alerts/`)
      .pipe(map(unwrapList));
  }
}

