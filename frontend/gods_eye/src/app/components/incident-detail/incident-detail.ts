import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MediaUrlService } from '../../core/services/media-url.service';
import { IncidentService } from '../../core/services/incident';
import { EvidenceService } from '../../core/services/evidence';
import { Incident } from '../../core/models/incident.model';
import { Evidence } from '../../core/models/evidence.model';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Component({
  selector: 'app-incident-detail',
  standalone: false,
  templateUrl: './incident-detail.html',
  styleUrl: './incident-detail.css',
})
export class IncidentDetail implements OnInit {
  incident: Incident | null = null;
  evidence: Evidence[] = [];
  isLoading = true;
  /** Set when the incident cannot be loaded (missing id, 403/404, or network). */
  loadError: string | null = null;
  selectedEvidence: Evidence | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private incidentService: IncidentService,
    private evidenceService: EvidenceService,
    private mediaUrl: MediaUrlService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const raw = this.route.snapshot.params['id'];
    const id = Number(raw);
    if (raw === undefined || raw === null || Number.isNaN(id) || id < 1) {
      this.loadError = 'Invalid incident link.';
      this.isLoading = false;
      return;
    }
    this.loadIncidentDetails(id);
  }

  loadIncidentDetails(id: number): void {
    this.loadError = null;
    forkJoin({
      incident: this.incidentService.getIncident(id).pipe(
        catchError(() => {
          this.loadError =
            'Could not load this incident. It may not exist or your account may not have access.';
          return of(null as Incident | null);
        }),
      ),
      evidence: this.evidenceService.getEvidence(id).pipe(catchError(() => of([] as Evidence[]))),
    }).subscribe({
      next: (results) => {
        if (!results.incident) {
          this.incident = null;
          if (!this.loadError) {
            this.loadError = 'Incident not found.';
          }
        } else {
          this.incident = results.incident;
          this.evidence = results.evidence;
        }
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading incident details:', err);
        this.loadError = 'Could not load incident details.';
        this.isLoading = false;
        this.cdr.detectChanges();
      },
    });
  }

  // Removed loadEvidence method - now handled by forkJoin above

  viewEvidence(evidence: Evidence): void {
    this.selectedEvidence = evidence;
  }

  closeModal(): void {
    this.selectedEvidence = null;
  }

  goBack(): void {
    this.router.navigate(['/incidents']);
  }

  mediaSrc(path: string | null | undefined): string {
    return this.mediaUrl.mediaUrl(path);
  }
}

