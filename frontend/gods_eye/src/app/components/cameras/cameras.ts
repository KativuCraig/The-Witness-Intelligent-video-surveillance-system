import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { CameraService } from '../../core/services/camera';
import { MediaUrlService } from '../../core/services/media-url.service';
import { liveHttpCandidateUrls } from '../../core/utils/live-stream-urls';
import { Camera } from '../../core/models/camera.model';

@Component({
  selector: 'app-cameras',
  standalone: false,
  templateUrl: './cameras.html',
  styleUrl: './cameras.css',
})
export class Cameras implements OnInit {
  cameras: Camera[] = [];
  isLoading = true;
  /** Shown when toggling Active fails (e.g. network or permission). */
  patchError: string | null = null;
  private thumbUrlAttempt: Record<number, number> = {};
  private lastCamerasKey = '';

  constructor(
    private cameraService: CameraService,
    private mediaUrl: MediaUrlService,
    private sanitizer: DomSanitizer,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  setActive(camera: Camera, active: boolean): void {
    if (camera.is_active === active) {
      return;
    }
    this.patchError = null;
    this.cameraService.patchCamera(camera.id, { is_active: active }).subscribe({
      next: (updated) => {
        camera.is_active = updated.is_active;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('patchCamera', err);
        this.patchError = 'Could not update camera. Check your connection and try again.';
        this.cdr.detectChanges();
      },
    });
  }

  ngOnInit(): void {
    this.loadCameras();
  }

  loadCameras(): void {
    this.cameraService.getCameras().subscribe({
      next: (cameras) => {
        const key = cameras.map((c) => `${c.id}:${c.stream_url}`).join('|');
        if (key !== this.lastCamerasKey) {
          this.lastCamerasKey = key;
          this.thumbUrlAttempt = {};
        }
        this.cameras = cameras;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading cameras:', err);
        this.isLoading = false;
        this.cdr.detectChanges();
      },
    });
  }

  addCamera(): void {
    this.router.navigate(['/cameras/new']);
  }

  openMonitor(): void {
    this.router.navigate(['/cameras/monitor']);
  }

  hasLiveHttpPreview(camera: Camera): boolean {
    const u = (camera.stream_url || '').trim().toLowerCase();
    return camera.source_type === 'LIVE' && (u.startsWith('http://') || u.startsWith('https://'));
  }

  liveThumbUrl(camera: Camera): SafeResourceUrl {
    const cands = liveHttpCandidateUrls(camera.stream_url || '');
    const idx = this.thumbUrlAttempt[camera.id] ?? 0;
    const raw = cands[idx] || cands[0] || '';
    return this.sanitizer.bypassSecurityTrustResourceUrl(raw || 'about:blank');
  }

  onThumbError(camera: Camera): void {
    const cands = liveHttpCandidateUrls(camera.stream_url || '');
    const idx = this.thumbUrlAttempt[camera.id] ?? 0;
    if (idx + 1 < cands.length) {
      this.thumbUrlAttempt[camera.id] = idx + 1;
      this.cdr.detectChanges();
    }
  }

  uploadThumbUrl(camera: Camera): string {
    return this.mediaUrl.mediaUrl(camera.video_file);
  }

  truncateUrl(url: string | null | undefined, max = 48): string {
    const s = (url || '').trim();
    if (s.length <= max) {
      return s;
    }
    return s.slice(0, max - 1) + '…';
  }
}
