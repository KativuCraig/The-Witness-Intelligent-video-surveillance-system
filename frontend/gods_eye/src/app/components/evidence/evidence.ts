import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { EvidenceService } from '../../core/services/evidence';
import { MediaUrlService } from '../../core/services/media-url.service';
import { Evidence as EvidenceModel } from '../../core/models/evidence.model';

@Component({
  selector: 'app-evidence',
  standalone: false,
  templateUrl: './evidence.html',
  styleUrl: './evidence.css',
})
export class Evidence implements OnInit {
  evidenceList: EvidenceModel[] = [];
  isLoading = true;
  selectedEvidence: EvidenceModel | null = null;

  constructor(
    private evidenceService: EvidenceService,
    private mediaUrl: MediaUrlService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadEvidence();
  }

  loadEvidence(): void {
    this.evidenceService.getEvidence().subscribe({
      next: (evidence) => {
        this.evidenceList = evidence;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading evidence:', err);
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  viewEvidence(evidence: EvidenceModel): void {
    this.selectedEvidence = evidence;
  }

  closeModal(): void {
    this.selectedEvidence = null;
  }

  mediaSrc(path: string | null | undefined): string {
    return this.mediaUrl.mediaUrl(path);
  }
}

