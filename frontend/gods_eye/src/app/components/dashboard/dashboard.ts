import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { Auth } from '../../core/services/auth';
import { CameraService } from '../../core/services/camera';
import { IncidentService } from '../../core/services/incident';
import { AlertService } from '../../core/services/alert';
import { Camera } from '../../core/models/camera.model';
import { Incident } from '../../core/models/incident.model';
import { Alert } from '../../core/models/alert.model';
import { interval, Subscription, forkJoin, of } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  standalone: false,
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit, OnDestroy {
  cameras: Camera[] = [];
  incidents: Incident[] = [];
  alerts: Alert[] = [];
  isLoading = true;
  private refreshSubscription?: Subscription;

  constructor(
    public authService: Auth,
    private cameraService: CameraService,
    private incidentService: IncidentService,
    private alertService: AlertService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadDashboardData();
    // Refresh data every 10 seconds
    this.refreshSubscription = interval(10000).subscribe(() => {
      this.loadDashboardData();
    });
  }

  ngOnDestroy(): void {
    this.refreshSubscription?.unsubscribe();
  }

  loadDashboardData(): void {
    const user = this.authService.getCurrentUser();
    
    const requests: any = {};

    if (user?.role === 'ADMIN') {
      requests.cameras = this.cameraService.getCameras();
      requests.incidents = this.incidentService.getIncidents();
      requests.alerts = this.alertService.getAlerts();
    } else if (user?.role === 'SECURITY') {
      requests.incidents = this.incidentService.getIncidents();
      requests.alerts = this.alertService.getAlerts();
    } else if (user?.role === 'VIEWER') {
      requests.alerts = this.alertService.getAlerts();
    }

    if (Object.keys(requests).length > 0) {
      forkJoin(requests).subscribe({
        next: (results: any) => {
          if (results.cameras) {
            this.cameras = results.cameras;
          }
          if (results.incidents) {
            this.incidents = results.incidents.slice(0, 5);
          }
          if (results.alerts) {
            this.alerts = results.alerts.slice(0, 5);
          }
          this.isLoading = false;
          this.cdr.detectChanges();
        },
        error: (err) => {
          console.error('Error loading dashboard data:', err);
          this.isLoading = false;
          this.cdr.detectChanges();
        }
      });
    } else {
      this.isLoading = false;
      this.cdr.detectChanges();
    }
  }

  hasRole(roles: string[]): boolean {
    return this.authService.hasRole(roles);
  }

  get recentIncidents(): Incident[] {
    return this.incidents.filter(i => i.status === 'NEW').slice(0, 3);
  }

  get activeCameras(): Camera[] {
    return this.cameras.filter(c => c.is_active);
  }
}

