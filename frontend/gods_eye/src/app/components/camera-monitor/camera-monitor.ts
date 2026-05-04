import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { CameraService } from '../../core/services/camera';
import { MediaUrlService } from '../../core/services/media-url.service';
import { liveHttpCandidateUrls } from '../../core/utils/live-stream-urls';
import { Camera } from '../../core/models/camera.model';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-camera-monitor',
  standalone: false,
  templateUrl: './camera-monitor.html',
  styleUrl: './camera-monitor.css',
})
export class CameraMonitor implements OnInit, OnDestroy {
  cameras: Camera[] = [];
  /** Active sources we attempt to preview (LIVE with URL, or UPLOAD with file). */
  previewCameras: Camera[] = [];
  isLoading = true;
  private refreshSubscription?: Subscription;
  /** Per-camera index into ``liveHttpCandidateUrls`` when the MJPEG path was omitted. */
  private liveUrlAttempt: Record<number, number> = {};
  /** No candidate produced a visible frame. */
  brokenLiveIds = new Set<number>();
  private lastSourcesKey = '';

  constructor(
    private cameraService: CameraService,
    private mediaUrl: MediaUrlService,
    private sanitizer: DomSanitizer,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.loadCameras();
    this.refreshSubscription = interval(5000).subscribe(() => this.loadCameras());
  }

  ngOnDestroy(): void {
    this.refreshSubscription?.unsubscribe();
  }

  loadCameras(): void {
    this.cameraService.getCameras().subscribe({
      next: (cameras) => {
        const key = cameras.map((c) => `${c.id}:${c.stream_url}:${c.is_active}`).join('|');
        if (key !== this.lastSourcesKey) {
          this.lastSourcesKey = key;
          this.liveUrlAttempt = {};
          this.brokenLiveIds.clear();
        }
        this.cameras = cameras;
        this.previewCameras = cameras.filter(
          (c) =>
            c.is_active &&
            ((c.source_type === 'LIVE' && !!c.stream_url?.trim()) ||
              (c.source_type === 'UPLOAD' && !!c.video_file)),
        );
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

  liveDisplayMode(camera: Camera): 'http' | 'rtsp' | 'none' {
    const u = (camera.stream_url || '').trim().toLowerCase();
    if (!u) {
      return 'none';
    }
    if (u.startsWith('rtsp://') || u.startsWith('rtsps://')) {
      return 'rtsp';
    }
    if (u.startsWith('http://') || u.startsWith('https://')) {
      return 'http';
    }
    return 'none';
  }

  private currentLiveHttpUrl(camera: Camera): string {
    const cands = liveHttpCandidateUrls(camera.stream_url || '');
    const idx = this.liveUrlAttempt[camera.id] ?? 0;
    return cands[idx] || cands[0] || '';
  }

  trustedLiveUrl(camera: Camera): SafeResourceUrl {
    if (this.liveDisplayMode(camera) !== 'http') {
      return this.sanitizer.bypassSecurityTrustResourceUrl('about:blank');
    }
    const u = this.currentLiveHttpUrl(camera);
    if (!u) {
      return this.sanitizer.bypassSecurityTrustResourceUrl('about:blank');
    }
    return this.sanitizer.bypassSecurityTrustResourceUrl(u);
  }

  uploadVideoUrl(camera: Camera): string {
    return this.mediaUrl.mediaUrl(camera.video_file);
  }

  onLiveError(camera: Camera): void {
    const cands = liveHttpCandidateUrls(camera.stream_url || '');
    const idx = this.liveUrlAttempt[camera.id] ?? 0;
    if (idx + 1 < cands.length) {
      this.liveUrlAttempt[camera.id] = idx + 1;
    } else {
      this.brokenLiveIds.add(camera.id);
    }
    this.cdr.detectChanges();
  }

  liveFailed(camera: Camera): boolean {
    return this.brokenLiveIds.has(camera.id);
  }

  truncateUrl(url: string | null | undefined, max = 56): string {
    const s = (url || '').trim();
    if (s.length <= max) {
      return s;
    }
    return s.slice(0, max - 1) + '…';
  }

  /** URL currently used for the live tile (after auto-retry). */
  effectiveLiveUrl(camera: Camera): string {
    return this.currentLiveHttpUrl(camera);
  }
}
