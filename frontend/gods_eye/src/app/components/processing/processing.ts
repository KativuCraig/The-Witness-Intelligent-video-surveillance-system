import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { IncidentService } from '../../core/services/incident';
import { EvidenceService } from '../../core/services/evidence';
import { CameraService } from '../../core/services/camera';
import { MediaUrlService } from '../../core/services/media-url.service';
import { Incident } from '../../core/models/incident.model';
import { Evidence } from '../../core/models/evidence.model';
import { Camera } from '../../core/models/camera.model';
import { timer, Subscription, of, forkJoin } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';

@Component({
  selector: 'app-processing',
  standalone: false,
  templateUrl: './processing.html',
  styleUrl: './processing.css',
})
export class Processing implements OnInit, OnDestroy {
  videoId!: number;
  camera: Camera | null = null;
  incidents: Incident[] = [];
  evidenceMap: { [incidentId: number]: Evidence[] } = {};
  isLoading = true;
  statusMessage = 'Waiting for processing to start...';

  private refreshSub?: Subscription;
  selectedEvidence: Evidence | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private incidentService: IncidentService,
    private evidenceService: EvidenceService,
    private cameraService: CameraService,
    private mediaUrl: MediaUrlService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      this.router.navigate(['/cameras']);
      return;
    }
    const parsed = Number(id);
    if (!Number.isFinite(parsed) || parsed < 1) {
      this.router.navigate(['/cameras']);
      return;
    }
    this.videoId = parsed;
    this.loadCamera();

    // Poll immediately, then every 5s. Stop when processed_file available.
    this.refreshSub = timer(0, 5000)
      .pipe(
        switchMap(() =>
          forkJoin([
            this.incidentService.getIncidents().pipe(catchError(err => {
              console.error('Error fetching incidents', err);
              return of([] as Incident[]);
            })),
            this.cameraService.getCamera(this.videoId).pipe(catchError(err => {
              // If camera not yet available, return null and continue polling
              console.warn('Error fetching camera', err);
              return of(null as any);
            }))
          ])
        )
      )
      .subscribe({
        next: ([incidents, camera]) => {
          if (camera) this.camera = camera as Camera;

          const filtered = (incidents as Incident[]).filter(i => i.video_source === this.videoId);
          this.incidents = filtered;

          if (this.incidents.length > 0) this.statusMessage = 'Processing: incidents detected';
          else this.statusMessage = 'Processing: no incidents yet';

          // fetch evidence for any incidents not yet in map
          this.incidents.forEach(i => {
            if (!this.evidenceMap[i.id]) {
              this.evidenceService.getEvidence(i.id).subscribe({
                next: (ev) => {
                  this.evidenceMap[i.id] = ev;
                  this.cdr.detectChanges();
                },
                error: (err) => {
                  console.error('Error loading evidence for', i.id, err);
                }
              });
            }
          });

          // If backend has saved processed file to the camera (processed_file), stop polling
          if (this.camera && (this.camera as any).processed_file) {
            this.statusMessage = 'Processing complete';
            // stop polling
            this.refreshSub?.unsubscribe();
            this.refreshSub = undefined;
          }

          this.isLoading = false;
          this.cdr.detectChanges();
        },
        error: (err) => {
          console.error('Polling subscription error', err);
        }
      });
  }

  ngOnDestroy(): void {
    this.refreshSub?.unsubscribe();
  }

  loadCamera(): void {
    this.cameraService.getCameras().subscribe({
      next: (cams) => {
        this.camera = cams.find(c => c.id === this.videoId) || null;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading camera info', err);
      }
    });
  }

  getMediaUrl(url: string | null): string {
    return this.mediaUrl.mediaUrl(url);
  }

  openEvidence(ev: Evidence): void {
    this.selectedEvidence = ev;
  }

  closeModal(): void {
    this.selectedEvidence = null;
  }

  // expose processed_file (backend may set this on VideoSource) in a safe way for templates
  get processedFile(): string | null {
    return (this.camera as any)?.processed_file || null;
  }
}
