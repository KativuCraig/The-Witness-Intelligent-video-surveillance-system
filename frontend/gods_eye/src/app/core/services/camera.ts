import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_URL } from '../config/api.config';
import { Camera, CreateCameraRequest } from '../models/camera.model';
import { unwrapList } from '../utils/api-response';

@Injectable({
  providedIn: 'root',
})
export class CameraService {
  private readonly apiUrl = API_URL;

  constructor(private http: HttpClient) {}

  getCameras(): Observable<Camera[]> {
    const token = localStorage.getItem('auth_token');
    const headers = token ? new HttpHeaders({ Authorization: `Token ${token}` }) : undefined;
    return this.http
      .get<Camera[] | { results: Camera[] }>(`${this.apiUrl}/cameras/`, headers ? { headers } : {})
      .pipe(map(unwrapList));
  }

  getCamera(id: number): Observable<Camera> {
    const token = localStorage.getItem('auth_token');
    const headers = token ? new HttpHeaders({ Authorization: `Token ${token}` }) : undefined;
    return this.http.get<Camera>(`${this.apiUrl}/cameras/${id}/`, headers ? { headers } : {});
  }

  createCamera(camera: CreateCameraRequest): Observable<Camera> {
    const formData = new FormData();
    formData.append('name', camera.name);
    formData.append('source_type', camera.source_type);
    
    if (camera.source_type === 'LIVE' && camera.stream_url) {
      formData.append('stream_url', camera.stream_url);
    }
    
    if (camera.source_type === 'UPLOAD' && camera.video_file) {
      formData.append('video_file', camera.video_file);
    }
    
    // Attach auth token if available
    const token = localStorage.getItem('auth_token');
    let options = {} as { headers?: HttpHeaders };
    if (token) {
      options.headers = new HttpHeaders({ Authorization: `Token ${token}` });
    }

    return this.http.post<Camera>(`${this.apiUrl}/cameras/`, formData, options);
  }

  patchCamera(
    id: number,
    body: Partial<{ is_active: boolean; name: string; stream_url: string | null }>,
  ): Observable<Camera> {
    const token = localStorage.getItem('auth_token');
    let headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    if (token) {
      headers = headers.set('Authorization', `Token ${token}`);
    }
    return this.http.patch<Camera>(`${this.apiUrl}/cameras/${id}/`, body, { headers });
  }
}

