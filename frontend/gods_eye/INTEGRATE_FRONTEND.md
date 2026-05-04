## Integrating the backend changes with your Angular frontend

This document explains how to integrate the backend changes we made in this session with an Angular frontend running on `http://localhost:4200`.

What you get from the backend (summary)
- Upload a video (as `VideoSource` with `source_type='UPLOAD'`) via the cameras API. The server will automatically start background processing on save.
- The detector will create `Incident` rows for frames that contain class `0` (VIOLENCE) above the configured confidence.
- For each created incident an `Evidence` record may contain an `image_frame` (JPEG saved under `MEDIA_ROOT/frames/...`). These are served under Django's `MEDIA_URL` when `DEBUG=True`.
- The following API routes are available (base path `/api/`):
  - `POST /api/cameras/` (VideoSource viewset) — create/upload video (Admin only by current permissions)
  - `GET /api/incidents/` — list incidents (Admin and Security)
  - `GET /api/evidence/?incident=<id>` — list evidence for an incident (Security)

Note about roles & auth
- The backend uses token/session auth (DRF). The endpoints are permissioned: uploading `VideoSource` currently requires the `IsAdmin` permission in `cameras.views.VideoSourceViewSet`. Incidents are only visible to `ADMIN` and `SECURITY` roles. Evidence is limited to `SECURITY`.
- Your frontend must authenticate users and include an Authorization header: `Authorization: Token <token>` (or use session cookies if you prefer).

API / data shapes
- Video upload (`POST /api/cameras/`) — multipart/form-data fields:
  - `name` (string) — name of the video source
  - `source_type` (string) — use `UPLOAD`
  - `video_file` (file) — the uploaded file

Example JSON response when creating a VideoSource (DRF default):
```json
{
  "id": 7,
  "name": "test upload",
  "source_type": "UPLOAD",
  "stream_url": null,
  "video_file": "videos/your_filename.mp4",
  "is_active": true,
  "created_at": "2026-02-26T12:00:00Z"
}
```

- Incident object (`/api/incidents/`): fields include `id`, `incident_type`, `confidence`, `detected_at`, `created_at`, `video_source` (id) and `video_source_name`.
- Evidence object (`/api/evidence/?incident=<id>`): serializer currently returns all Evidence fields, including `image_frame` (string URL when returned by DRF) and `timestamp`.

Example detection JSON fragment (from `infer_video` output):
```json
{
  "frame_index": 2,
  "boxes": [
    {
      "xyxy": [[786.66, 124.03, 931.95, 406.00]],
      "conf": 0.26456835865974426,
      "class": 0
    }
  ]
}
```

Frontend integration patterns

1) Upload video (Admin user flow)

Use Angular's `HttpClient` and `FormData` to upload the file. Example service method:

```ts
// src/app/services/upload.service.ts
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class UploadService {
  private api = '/api/cameras/';

  constructor(private http: HttpClient) {}

  uploadVideo(file: File, name: string, token: string) {
    const fd = new FormData();
    fd.append('name', name);
    fd.append('source_type', 'UPLOAD');
    fd.append('video_file', file, file.name);

    const headers = new HttpHeaders({
      Authorization: `Token ${token}`
    });

    return this.http.post(this.api, fd, { headers });
  }
}
```

Call this from a component that accepts a file input and shows upload progress.

2) Poll for processing results

Processing runs asynchronously on the server after upload. You can poll the incidents endpoint for new incidents for the uploaded `video_source` id. Since the current `IncidentViewSet` doesn't support server-side filtering by `video_source`, request all incidents and filter on the frontend (or add server-side filtering in a backend change).

Example polling service:

```ts
// src/app/services/monitor.service.ts
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { interval, Observable } from 'rxjs';
import { switchMap } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class MonitorService {
  private incidentsApi = '/api/incidents/';

  constructor(private http: HttpClient) {}

  pollIncidents(token: string, pollMs = 5000): Observable<any> {
    const headers = { Authorization: `Token ${token}` };
    return interval(pollMs).pipe(switchMap(() => this.http.get(this.incidentsApi, { headers })));
  }
}
```

Filter the returned incidents for those with `video_source === <your id>` on the client and display them.

3) Fetch evidence images and display them

When an `Incident` exists, call `GET /api/evidence/?incident=<id>` with the proper auth header and take the `image_frame` field from the serializer. That value will be a path like `frames/<filename>.jpg` — to render it in the browser, prepend the server origin + MEDIA_URL (e.g., `http://localhost:8000/media/frames/<filename>.jpg`) or use the absolute URL DRF provides when configured.

Example usage:

```ts
// component.ts
this.http.get(`/api/evidence/?incident=${incidentId}`, { headers }).subscribe((evidenceList:any) => {
  this.images = evidenceList.map((e:any) => `${window.location.origin}${'/media/'}${e.image_frame}`);
});
```

In your template:

```html
<div *ngFor="let img of images">
  <img [src]="img" alt="evidence" style="max-width:300px;" />
</div>
```

Notes about annotated video and frontend playback
- The backend currently writes annotated outputs to `runs/detect/exp*/`. Those files are not automatically in `MEDIA_ROOT`. To make annotated video available via Django `MEDIA_URL` you can:
  1. Update `VideoSource` to include a `processed_file = models.FileField(upload_to='annotated/', blank=True, null=True)` and copy the annotated file into `MEDIA_ROOT/annotated/`, then set `video_source.processed_file` to the saved file path in the processing logic. The frontend can then show `video_source.processed_file.url`.
  2. Or, copy/symlink the annotated file into `MEDIA_ROOT/` after processing and expose its URL.

If you want, I can implement option (1) (add `processed_file` to `VideoSource` and save annotated file during processing) — that will allow the frontend to fetch the processed video URL via the `VideoSource` representation.

Auth/CORS and local dev
- `gods_eye/settings.py` already allows CORS for `http://localhost:4200`. Ensure your Angular app runs from that origin or add your origin to `CORS_ALLOWED_ORIGINS`.
- Use token auth in headers for all API calls. If you prefer sessions, ensure cookies are sent cross-site or enable same-origin dev setup.

Realtime alternative
- If you want real-time updates instead of polling, implement a simple WebSocket (Django Channels) or use a lightweight SSE/webhook mechanism that notifies the frontend when processing completes for a `VideoSource`.

Troubleshooting
- 401 / permission errors: ensure the requesting user has correct role (`ADMIN` for upload; `SECURITY` or `ADMIN` for incidents/evidence) and that the token is valid.
- Large video uploads: webserver / Django configurations may limit upload size. Consider uploading directly to S3 and saving the URL in `VideoSource`.
- Processing time: video inference is CPU/GPU intensive — show a spinner and use polling frequency of 5–10s.

Next steps I can implement for you (pick any):
- Add `processed_file` FileField to `VideoSource` and copy annotated outputs into `MEDIA_ROOT/annotated/` so the frontend can immediately GET the processed video URL.
- Add server-side filtering for `IncidentViewSet` by `video_source` (so the frontend can call `/api/incidents/?video_source=7`).
- Add `min_conf` or `dedup_seconds` options to processing so frontend sees fewer false or duplicate incidents.
- Add a small example Angular component/repo with working upload/poll/display code.

If you want me to commit any of the backend changes above (e.g., `processed_file` on `VideoSource`, `IncidentViewSet` filtering, example Angular component), tell me which one and I will implement it next.
