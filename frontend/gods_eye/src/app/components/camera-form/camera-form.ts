import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { CameraService } from '../../core/services/camera';

@Component({
  selector: 'app-camera-form',
  standalone: false,
  templateUrl: './camera-form.html',
  styleUrl: './camera-form.css',
})
export class CameraForm {
  cameraForm: FormGroup;
  isLoading = false;
  errorMessage = '';
  selectedFile: File | null = null;

  constructor(
    private fb: FormBuilder,
    private cameraService: CameraService,
    private router: Router
  ) {
    this.cameraForm = this.fb.group({
      name: ['', Validators.required],
      source_type: ['LIVE', Validators.required],
      stream_url: ['']
    });

    this.cameraForm.get('source_type')?.valueChanges.subscribe(value => {
      if (value === 'LIVE') {
        this.cameraForm.get('stream_url')?.setValidators([Validators.required]);
      } else {
        this.cameraForm.get('stream_url')?.clearValidators();
      }
      this.cameraForm.get('stream_url')?.updateValueAndValidity();
    });
  }

  onFileSelect(event: any): void {
    if (event.target.files.length > 0) {
      this.selectedFile = event.target.files[0];
    }
  }

  onSubmit(): void {
    if (this.cameraForm.invalid) {
      return;
    }

    const sourceType = this.cameraForm.value.source_type;
    if (sourceType === 'UPLOAD' && !this.selectedFile) {
      this.errorMessage = 'Please select a video file';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    const cameraData = {
      name: this.cameraForm.value.name,
      source_type: sourceType,
      stream_url: sourceType === 'LIVE' ? this.cameraForm.value.stream_url : null,
      video_file: sourceType === 'UPLOAD' ? this.selectedFile : null
    };

    this.cameraService.createCamera(cameraData).subscribe({
      next: (created) => {
        this.isLoading = false;
        // If upload, navigate to processing page for this video source
        if (created && created.id && sourceType === 'UPLOAD') {
          this.router.navigate(['/processing', created.id]);
        } else {
          this.router.navigate(['/cameras']);
        }
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = 'Failed to create camera';
        console.error('Error creating camera:', err);
      }
    });
  }

  cancel(): void {
    this.router.navigate(['/cameras']);
  }
}

