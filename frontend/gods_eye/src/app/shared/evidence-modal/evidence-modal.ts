import { Component, Input, Output, EventEmitter } from '@angular/core';
import { Evidence } from '../../core/models/evidence.model';
import { MediaUrlService } from '../../core/services/media-url.service';

@Component({
  selector: 'app-evidence-modal',
  standalone: false,
  templateUrl: './evidence-modal.html',
  styleUrl: './evidence-modal.css',
})
export class EvidenceModal {
  @Input() evidence: Evidence | null = null;
  @Output() close = new EventEmitter<void>();

  constructor(private mediaUrl: MediaUrlService) {}

  closeModal(): void {
    this.close.emit();
  }

  getMediaUrl(url: string | null): string {
    return this.mediaUrl.mediaUrl(url);
  }
}

